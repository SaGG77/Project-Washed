# Librerias
from datetime import date, datetime, timedelta
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
# Instancia de base de datos
from extensions import db
# Modelos
from models.habit import Habit
from models.habit_log import HabitLog
# Decorador proteger rutas
from utils.auth import login_required

habit_bp = Blueprint("habit", __name__)

def _parse_date_or_today(raw_date: str | None) -> date:
    """
    Convierte un texto YYYY-MM-DD a objeto date.

    Si viene vacío o inválido, devuelve la fecha de hoy para tener un fallback seguro.
    """
    # Si no viene nada (?date=...)
    if not raw_date:
        return date.today()

    try:
        # Intentamos parsear el formato esperado.
        return datetime.strptime(raw_date, "%Y-%m-%d").date()
    except ValueError:
        # Si el formato es inválido (ej: 2026/01/40), volvemos a hoy.
        return date.today()


def _build_streak(completed_dates: set[date]) -> tuple[int, int]:
    """
    Calcula:
    - racha actual (current_streak)
    - mejor racha histórica (best_streak)

    Reglas usadas:
    - Best streak: mayor secuencia de días consecutivos en completed_dates.
    - Current streak: si hoy está completado, arrancamos desde hoy;
      si no, pero ayer sí, arrancamos desde ayer;
      si no hay ni hoy ni ayer, racha actual = 0.
    """
    # Sin datos, ambas rachas son 0.
    if not completed_dates:
        return 0, 0

    # Ordenamos para detectar secuencias consecutivas día a día.
    sorted_dates = sorted(completed_dates)

    # Inicializamos rachas en 1 porque ya hay al menos una fecha.
    best_streak = 1
    current_run = 1

    # Recorremos desde el segundo elemento comparando con el anterior.
    for idx in range(1, len(sorted_dates)):
        # Si el día actual es exactamente el siguiente al anterior, seguimos racha.
        if sorted_dates[idx] == sorted_dates[idx - 1] + timedelta(days=1):
            current_run += 1
            best_streak = max(best_streak, current_run)
        # Si no es consecutivo (y tampoco duplicado), reiniciamos run.
        elif sorted_dates[idx] != sorted_dates[idx - 1]:
            current_run = 1

    # Calculamos racha actual con referencia en hoy/ayer.
    today = date.today()
    yesterday = today - timedelta(days=1)

    if today in completed_dates:
        # Si completó hoy, la racha actual puede seguir viva desde hoy.
        cursor = today
    elif yesterday in completed_dates:
        # Si no completó hoy pero sí ayer, cuenta racha hasta ayer.
        cursor = yesterday
    else:
        # Si no hay ni hoy ni ayer, no hay racha vigente.
        return 0, best_streak

    # Contamos hacia atrás mientras haya días consecutivos completados.
    current_streak = 0
    while cursor in completed_dates:
        current_streak += 1
        cursor -= timedelta(days=1)

    return current_streak, best_streak


@habit_bp.route("/habits", methods=["GET", "POST"])
@login_required
def habits():
    """
    GET:
      - Lista hábitos del usuario logueado.
      - Permite filtrar visualización por fecha (?date=YYYY-MM-DD).
      - Mapea logs del día por habit_id para mostrar estado rápido.

    POST:
      - Crea un nuevo hábito.
    """
    # Leemos el user_id de la sesión para aislar datos por usuario.
    user_id = session["user_id"]

    # Flujo de creación de hábito.
    if request.method == "POST":
        # Capturamos y limpiamos inputs del formulario.
        name = request.form.get("name", "").strip()
        target_minutes_raw = request.form.get("target_minutes", "").strip()
        is_active = request.form.get("is_active") == "on"

        # Validación básica: nombre obligatorio.
        if not name:
            flash("El nombre del hábito es obligatorio.", "warning")
            return redirect(url_for("habit.habits"))

        # Meta de minutos es opcional.
        target_minutes = None
        if target_minutes_raw:
            try:
                target_minutes = int(target_minutes_raw)
            except ValueError:
                flash("La meta de minutos debe ser un número entero.", "warning")
                return redirect(url_for("habit.habits"))

            # Evitamos metas no positivas.
            if target_minutes <= 0:
                flash("La meta de minutos debe ser mayor a 0.", "warning")
                return redirect(url_for("habit.habits"))

        # Construimos la entidad Habit con los datos validados.
        habit = Habit(
            user_id=user_id,
            name=name,
            target_minutes=target_minutes,
            is_active=is_active,
        )

        # Persistimos cambios en DB.
        db.session.add(habit)
        db.session.commit()

        # Feedback visual al usuario.
        flash("Hábito creado.", "success")
        return redirect(url_for("habit.habits"))

    # Si es GET: cargamos hábitos del usuario más recientes primero.
    habits_data = Habit.query.filter_by(user_id=user_id).order_by(Habit.created_at.desc()).all()

    # Parseamos la fecha que llega por query string.
    selected_date = _parse_date_or_today(request.args.get("date"))

    # Armamos lista de IDs para consultar logs de ese día en 1 sola query.
    habit_ids = [habit.id for habit in habits_data]
    logs_by_habit = {}

    if habit_ids:
        logs = HabitLog.query.filter(
            HabitLog.habit_id.in_(habit_ids),
            HabitLog.log_date == selected_date,
        ).all()

        # Transformamos lista en diccionario {habit_id: log} para lookup rápido en template.
        logs_by_habit = {log.habit_id: log for log in logs}

    # Renderizamos vista principal de hábitos.
    return render_template(
        "habits/index.html",
        habits=habits_data,
        selected_date=selected_date,
        logs_by_habit=logs_by_habit,
    )


@habit_bp.route("/habits/<int:habit_id>/edit", methods=["GET", "POST"])
@login_required
def edit_habit(habit_id):
    """
    Permite editar un hábito propio.
    - GET: muestra formulario precargado.
    - POST: valida y guarda cambios.
    """
    user_id = session["user_id"]

    # Seguridad: solo se puede editar un hábito del usuario logueado.
    habit = Habit.query.filter_by(id=habit_id, user_id=user_id).first_or_404()

    if request.method == "POST":
        # Leemos valores del formulario.
        name = request.form.get("name", "").strip()
        target_minutes_raw = request.form.get("target_minutes", "").strip()
        is_active = request.form.get("is_active") == "on"

        # Validación de nombre.
        if not name:
            flash("El nombre del hábito es obligatorio.", "warning")
            return render_template("habits/edit.html", habit=habit)

        # Validación de meta opcional.
        target_minutes = None
        if target_minutes_raw:
            try:
                target_minutes = int(target_minutes_raw)
            except ValueError:
                flash("La meta de minutos debe ser un número entero.", "warning")
                return render_template("habits/edit.html", habit=habit)

            if target_minutes <= 0:
                flash("La meta de minutos debe ser mayor a 0.", "warning")
                return render_template("habits/edit.html", habit=habit)

        # Aplicamos cambios al modelo.
        habit.name = name
        habit.target_minutes = target_minutes
        habit.is_active = is_active

        # Guardamos en base de datos.
        db.session.commit()

        flash("Hábito actualizado.", "success")
        return redirect(url_for("habit.habits"))

    # GET: mostramos formulario de edición.
    return render_template("habits/edit.html", habit=habit)


@habit_bp.route("/habits/<int:habit_id>/delete", methods=["POST"])
@login_required
def delete_habit(habit_id):
    """Elimina un hábito propio."""
    user_id = session["user_id"]

    # Seguridad: no se puede borrar hábitos de otro usuario.
    habit = Habit.query.filter_by(id=habit_id, user_id=user_id).first_or_404()

    # Borramos hábito (y logs relacionados por cascade en el modelo).
    db.session.delete(habit)
    db.session.commit()

    flash("Hábito eliminado.", "success")
    return redirect(url_for("habit.habits"))


@habit_bp.route("/habits/<int:habit_id>/toggle", methods=["POST"])
@login_required
def toggle_habit(habit_id):
    """
    Alterna estado completado/no completado para un hábito en una fecha.

    - Si no existe log para ese día, lo crea como completado=True.
    - Si existe, invierte completed.
    - Minutos opcional: si se envía, se guarda/actualiza.
    """
    user_id = session["user_id"]

    # Seguridad: solo togglear hábitos propios.
    habit = Habit.query.filter_by(id=habit_id, user_id=user_id).first_or_404()

    # Fecha objetivo tomada de query param ?date=YYYY-MM-DD (o hoy por fallback).
    log_date = _parse_date_or_today(request.args.get("date"))

    # Buscamos log existente del hábito en esa fecha.
    log = HabitLog.query.filter_by(habit_id=habit.id, log_date=log_date).first()

    # Minutos opcionales desde el formulario.
    minutes_raw = request.form.get("minutes", "").strip()

    minutes = None
    if minutes_raw:
        try:
            minutes = int(minutes_raw)
            if minutes < 0:
                raise ValueError
        except ValueError:
            flash("Los minutos deben ser un número entero positivo.", "warning")
            return redirect(url_for("habit.habits", date=log_date.isoformat()))

    if log:
        # Ya existe registro diario: invertimos estado.
        log.completed = not log.completed

        # Solo actualizamos minutos si el usuario envió el campo.
        if minutes_raw:
            log.minutes = minutes
    else:
        # No existe registro: creamos uno marcado como completado.
        log = HabitLog(
            habit_id=habit.id,
            log_date=log_date,
            completed=True,
            minutes=minutes,
        )
        db.session.add(log)

    db.session.commit()
    flash("Registro actualizado.", "success")
    return redirect(url_for("habit.habits", date=log_date.isoformat()))


@habit_bp.route("/dashboard")
@login_required
def dashboard():
    """
    Dashboard con KPIs:
    - cumplimiento 7 y 30 días
    - días cumplidos 7/30
    - racha actual y mejor racha
    - top 5 hábitos por cantidad de logs completados
    """
    user_id = session["user_id"]

    # Para KPIs tomamos hábitos activos del usuario.
    habits_data = Habit.query.filter_by(user_id=user_id, is_active=True).all()

    # Extraemos IDs para consultar logs de una sola vez.
    habit_ids = [habit.id for habit in habits_data]
    logs = []

    if habit_ids:
        # Traemos solo logs marcados como completados.
        logs = HabitLog.query.filter(
            HabitLog.habit_id.in_(habit_ids),
            HabitLog.completed.is_(True),
        ).all()

    # Definimos cortes de ventana temporal (incluyendo hoy).
    today = date.today()
    since_7 = today - timedelta(days=6)   # hoy + 6 días atrás = 7 días
    since_30 = today - timedelta(days=29)  # hoy + 29 días atrás = 30 días

    # Contamos completados en cada ventana.
    completed_last_7 = sum(1 for log in logs if log.log_date >= since_7)
    completed_last_30 = sum(1 for log in logs if log.log_date >= since_30)

    # Posibles completados máximos = hábitos activos x cantidad de días de ventana.
    total_possible_7 = len(habits_data) * 7
    total_possible_30 = len(habits_data) * 30

    # Porcentaje de cumplimiento (evitamos división por cero si no hay hábitos).
    compliance_7 = round((completed_last_7 / total_possible_7) * 100, 1) if total_possible_7 else 0
    compliance_30 = round((completed_last_30 / total_possible_30) * 100, 1) if total_possible_30 else 0

    # Set de fechas completadas para calcular rachas globales.
    completed_dates = {log.log_date for log in logs}
    current_streak, best_streak = _build_streak(completed_dates)

    # Top hábitos: ordenamos por cantidad de completados.
    top_habits = []
    if habits_data:
        # Inicializamos conteo en 0 para todos los hábitos activos.
        log_count_by_habit = {habit.id: 0 for habit in habits_data}

        # Sumamos 1 por cada log completado.
        for log in logs:
            log_count_by_habit[log.habit_id] = log_count_by_habit.get(log.habit_id, 0) + 1

        # Orden descendente por conteo y nos quedamos con top 5.
        top_habits = sorted(
            habits_data,
            key=lambda habit: log_count_by_habit.get(habit.id, 0),
            reverse=True,
        )[:5]

    # Renderizamos dashboard con todos los KPI calculados.
    return render_template(
        "habits/dashboard.html",
        habits_count=len(habits_data),
        completed_last_7=completed_last_7,
        completed_last_30=completed_last_30,
        compliance_7=compliance_7,
        compliance_30=compliance_30,
        current_streak=current_streak,
        best_streak=best_streak,
        top_habits=top_habits,
    )