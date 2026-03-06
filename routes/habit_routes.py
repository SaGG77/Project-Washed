"""
routes/habit_routes.py

Este blueprint maneja TODO lo relacionado con hábitos:
- Pantallas HTML:
  - /habits (dashboard)
  - /habits/new (crear)
  - /habits/<id> (detalle)
  - /habits/<id>/edit (editar)
  - /habits/<id>/toggle_today (marcar/desmarcar hoy)
- APIs JSON para gráficos (Chart.js):
  - /api/habits/summary
  - /api/habits/<id>/series
  - /api/habits/<id>/heatmap
  - /api/habits/by_weekday
"""

from datetime import date
from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from extensions import db
from forms import HabitForm
from models.habit import Habit
from models.habit_log import HabitLog
from utils.auth import login_required

# Importamos funciones "puras" para métricas:
# Esto es excelente práctica porque:
# - Tu blueprint queda más corto y legible
# - Puedes testear métricas sin levantar Flask
from utils.habit_metrics import (
    calculate_streaks,
    clamp_range_days,
    global_completion_rate,
    global_streaks,
    habit_completed_dates,
    habit_completion_rate,
    summary_series_for_user,
    date_series,
    weekday_counts_for_user,
)

habit_bp = Blueprint("habit", __name__)


# -----------------------------
# RUTAS "NAVEGACIÓN"
# -----------------------------

@habit_bp.route("/index", methods=["GET"])
@login_required
def index():
    """
    /index => redirige al dashboard real.
    Esto sirve para mantener compatibilidad con tu app si antes entrabas por /index.
    """
    return redirect(url_for("habit.habits"))


# -----------------------------
# DASHBOARD
# -----------------------------

@habit_bp.route("/habits", methods=["GET"])
@login_required
def habits():
    """
    Dashboard:
    - lista hábitos del usuario
    - calcula métricas por hábito (cards)
    - calcula métricas globales (cards arriba)
    - renderiza habits/dashboard.html
    """
    user_id = session["user_id"]

    # 1) Traemos los hábitos del usuario (para cards).
    habits = (
        Habit.query
        .filter_by(user_id=user_id)
        .order_by(Habit.created_at.desc())
        .all()
    )

    # 2) Por cada hábito calculamos:
    # - racha actual / mejor racha
    # - % últimos 7 días
    # - si hoy está marcado
    habit_cards = []
    for habit in habits:
        completed_dates = habit_completed_dates(habit.id)  # set[date] (idealmente)
        current_streak, best_streak = calculate_streaks(completed_dates)

        habit_cards.append(
            {
                "habit": habit,
                "current_streak": current_streak,
                "best_streak": best_streak,
                "rate_7": habit_completion_rate(habit.id, 7),
                "today_marked": date.today() in completed_dates,
            }
        )

    # 3) Métricas globales:
    # - racha global (si tu función lo define así)
    # - % de cumplimiento 7 y 30 días
    current_streak, best_streak = global_streaks(user_id)

    return render_template(
        "habits/dashboard.html",
        habit_cards=habit_cards,
        current_streak=current_streak,
        best_streak=best_streak,
        completion_7=global_completion_rate(user_id, 7),
        completion_30=global_completion_rate(user_id, 30),
    )


# -----------------------------
# CREAR HÁBITO
# -----------------------------

@habit_bp.route("/habits/new", methods=["GET", "POST"])
@login_required
def new_habit():
    """
    GET  -> muestra el formulario
    POST -> valida y crea el hábito
    """
    user_id = session["user_id"]
    form = HabitForm()

    if form.validate_on_submit():
        habit = Habit(
            user_id=user_id,
            name=form.name.data.strip(),
            target_minutes=form.target_minutes.data,
            is_active=form.is_active.data,
        )
        db.session.add(habit)
        db.session.commit()

        flash("Hábito creado con éxito", "success")
        return redirect(url_for("habit.habits"))

    return render_template("habits/new.html", form=form)


# -----------------------------
# EDITAR HÁBITO
# -----------------------------

@habit_bp.route("/habits/<int:habit_id>/edit", methods=["GET", "POST"])
@login_required
def edit_habit(habit_id):
    """
    GET  -> muestra el formulario con datos del hábito
    POST -> guarda cambios
    """
    user_id = session["user_id"]

    habit = Habit.query.filter_by(id=habit_id, user_id=user_id).first_or_404()
    form = HabitForm(obj=habit)  # precarga el formulario con el objeto

    if form.validate_on_submit():
        # populate_obj copia los campos del form al modelo automáticamente.
        form.populate_obj(habit)

        # Limpieza: siempre guardamos el nombre sin espacios al inicio/final.
        habit.name = habit.name.strip()

        db.session.commit()
        flash("Hábito actualizado correctamente", "success")
        return redirect(url_for("habit.habits"))

    return render_template("habits/edit.html", form=form, habit=habit)


# -----------------------------
# MARCAR/DESMARCAR HOY
# -----------------------------

@habit_bp.route("/habits/<int:habit_id>/toggle_today", methods=["POST"])
@login_required
def toggle_today(habit_id):
    """
    Toggle:
    - si existe log hoy => lo borra (desmarcar)
    - si NO existe => lo crea (marcar)

    Nota: esto funciona BIEN si tienes constraint único (habit_id, log_date)
    en tu tabla habits_logs para evitar duplicados.
    """
    user_id = session["user_id"]
    habit = Habit.query.filter_by(id=habit_id, user_id=user_id).first_or_404()

    today = date.today()

    existing_log = HabitLog.query.filter_by(habit_id=habit.id, log_date=today).first()

    if existing_log:
        db.session.delete(existing_log)
        flash(f"Quitaste la marca de hoy para '{habit.name}'", "warning")
    else:
        # completed=True y minutes=0: depende de tu modelo,
        # pero lo dejamos como tu intención original.
        db.session.add(
            HabitLog(
                habit_id=habit.id,
                log_date=today,
                completed=True,
                minutes=0,
            )
        )
        flash(f"Marcaste hoy en '{habit.name}'", "success")

    db.session.commit()

    # Si el form manda "next", volvemos a donde estaba el usuario.
    next_url = request.form.get("next")
    if next_url:
        return redirect(next_url)

    # Si no hay next, vamos al detalle del hábito.
    return redirect(url_for("habit.habit_detail", habit_id=habit.id))


# -----------------------------
# DETALLE HÁBITO
# -----------------------------

@habit_bp.route("/habits/<int:habit_id>", methods=["GET"])
@login_required
def habit_detail(habit_id):
    """
    Pantalla detalle:
    - muestra métricas del hábito
    - la data de gráficos se carga por JS vía endpoints /api/...
    """
    user_id = session["user_id"]
    habit = Habit.query.filter_by(id=habit_id, user_id=user_id).first_or_404()

    completed_dates = habit_completed_dates(habit.id)
    current_streak, best_streak = calculate_streaks(completed_dates)

    return render_template(
        "habits/detail.html",
        habit=habit,
        today_marked=date.today() in completed_dates,
        current_streak=current_streak,
        best_streak=best_streak,
        total_completed=len(completed_dates),
        completion_30=habit_completion_rate(habit.id, 30),
    )


# -----------------------------
# APIs PARA GRÁFICOS
# -----------------------------

@habit_bp.route("/api/habits/summary", methods=["GET"])
@login_required
def habits_summary_api():
    """
    Devuelve datos globales para el dashboard:
    - series diario (labels/values) para tendencia
    - top hábitos (ej: % 30 días)
    """
    user_id = session["user_id"]

    # clamp_range_days evita que alguien pida 99999 días y reviente la app.
    range_days = clamp_range_days(int(request.args.get("range", 30)))

    payload = summary_series_for_user(user_id, range_days)

    return jsonify(
        {
            "range": range_days,
            "series": payload["series"],  # {labels: [...], values: [...]}
            "habits": payload["habits"],  # [{name, value}, ...]
        }
    )


@habit_bp.route("/api/habits/<int:habit_id>/series", methods=["GET"])
@login_required
def habit_series_api(habit_id):
    """
    Serie del hábito:
    labels: fechas ISO
    values: 1 si completó ese día, 0 si no
    """
    user_id = session["user_id"]
    habit = Habit.query.filter_by(id=habit_id, user_id=user_id).first_or_404()

    range_days = clamp_range_days(int(request.args.get("range", 90)))

    dates = date_series(range_days)
    labels = [d.isoformat() for d in dates]

    completed = habit_completed_dates(habit.id)
    values = [1 if d in completed else 0 for d in dates]

    return jsonify(
        {
            "habit": habit.name,
            "range": range_days,
            "labels": labels,
            "values": values,
        }
    )


@habit_bp.route("/api/habits/<int:habit_id>/heatmap", methods=["GET"])
@login_required
def habit_heatmap_api(habit_id):
    """
    Heatmap:
    - from/to: rango
    - completed_dates: lista de fechas completadas dentro del rango
    """
    user_id = session["user_id"]
    habit = Habit.query.filter_by(id=habit_id, user_id=user_id).first_or_404()

    range_days = clamp_range_days(int(request.args.get("range", 180)))

    dates = date_series(range_days)
    completed = habit_completed_dates(habit.id)

    return jsonify(
        {
            "habit": habit.name,
            "from": dates[0].isoformat(),
            "to": dates[-1].isoformat(),
            "completed_dates": [
                d.isoformat() for d in sorted(completed) if d >= dates[0]
            ],
        }
    )


@habit_bp.route("/api/habits/by_weekday", methods=["GET"])
@login_required
def habits_by_weekday_api():
    """
    Consistencia por día de la semana.
    labels: ["Lun","Mar",...]
    values: [conteos...]
    """
    user_id = session["user_id"]
    range_days = clamp_range_days(int(request.args.get("range", 90)))

    payload = weekday_counts_for_user(user_id, range_days)

    return jsonify(
        {
            "range": range_days,
            "labels": payload["labels"],
            "values": payload["values"],
        }
    )