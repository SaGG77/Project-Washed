"""
Utilidades de negocio para el módulo de hábitos.

IDEA CLAVE:
- Este archivo NO define rutas.
- Este archivo NO renderiza templates.
- Este archivo solo hace "cálculos" y "consultas" relacionadas con métricas.

Ventajas:
1) Mantienes routes/habit_routes.py limpio.
2) Puedes cambiar reglas (por ejemplo cómo se calcula racha) en un solo lugar.
3) Es más fácil testear porque son funciones sin HTML.
"""

from __future__ import annotations

# defaultdict(int) te da un diccionario que por defecto arranca en 0.
# Ej: counts_by_date[some_date] += 1 no falla aunque la clave no exista.
from collections import defaultdict

# date representa una fecha (año-mes-día) sin hora.
# timedelta representa una "duración", ej: 7 días.
from datetime import date, timedelta

# func te permite usar funciones SQL (COUNT, SUM, etc.) con SQLAlchemy.
from sqlalchemy import func

from extensions import db
from models.habit import Habit
from models.habit_log import HabitLog


def clamp_range_days(value: int, minimum: int = 1, maximum: int = 365) -> int:
    """
    Limita un rango de días a un intervalo seguro.

    ¿Por qué existe esto?
    - Porque tus endpoints /api aceptan un parámetro "range".
    - Alguien podría mandar range=999999 y te revienta el servidor (consulta gigante).
    - También evita valores inválidos como 0 o negativos.

    Ej:
    - clamp_range_days(0) -> 1
    - clamp_range_days(400) -> 365
    - clamp_range_days(30) -> 30
    """
    return max(minimum, min(value, maximum))


def date_series(days: int, end_date: date | None = None) -> list[date]:
    """
    Construye una lista continua de fechas, incluyendo la fecha final (end_date).

    Ejemplo:
    - days = 5, end_date = 2026-02-26
    -> [2026-02-22, 2026-02-23, 2026-02-24, 2026-02-25, 2026-02-26]

    ¿Para qué sirve?
    - Para generar labels del gráfico (Chart.js) y para comparar cada día con logs.
    """
    # Si no te pasan end_date, usamos el día de hoy.
    end_date = end_date or date.today()

    # start_date es "days-1" días antes, para que incluya el día final
    # Ej: days=1 => start_date = end_date (lista de un solo día)
    start_date = end_date - timedelta(days=days - 1)

    # Construimos la lista día por día
    return [start_date + timedelta(days=offset) for offset in range(days)]


def habit_completed_dates(habit_id: int) -> set[date]:
    """
    Devuelve un set de días completados para un hábito.

    ¿Por qué un set?
    - Porque luego preguntas "¿hoy está en completed_dates?"
      y eso en set es O(1) (rápido).
    - En lista sería O(n) (más lento si hay muchos días).

    Consulta:
    - Seleccionamos SOLO HabitLog.log_date (no todo el objeto), por eficiencia.
    - Filtramos por habit_id y completed=True.
    """
    rows = (
        db.session.query(HabitLog.log_date)
        .filter(
            HabitLog.habit_id == habit_id,
            HabitLog.completed.is_(True),
        )
        .all()
    )

    # rows es una lista de objetos tipo Row, donde row.log_date es un date.
    return {row.log_date for row in rows}


def calculate_streaks(completed_dates: set[date]) -> tuple[int, int]:
    """
    Calcula:
    - racha actual (current)
    - mejor racha histórica (best)
    usando un conjunto de fechas completadas.

    Definición que estás usando (muy buena y común):
    - Si hoy está marcado, racha actual se calcula contando hacia atrás desde hoy.
    - Si hoy NO está marcado, se calcula desde ayer (para no matar la racha antes de dormir).

    Importante:
    - Si no hay datos, no hay racha.
    """
    if not completed_dates:
        return 0, 0

    # ------------------------ Racha actual ------------------------
    today = date.today()
    current = 0

    # Cursor = hoy si hoy está completado, si no, arrancamos desde ayer.
    cursor = today if today in completed_dates else today - timedelta(days=1)

    # Mientras el cursor esté dentro del set, seguimos contando hacia atrás.
    while cursor in completed_dates:
        current += 1
        cursor -= timedelta(days=1)

    # ------------------------ Mejor racha histórica ------------------------
    # Esto recorre TODAS las fechas completadas en orden.
    # running = racha "en progreso"
    # best = máximo alcanzado
    best = 0
    running = 0
    previous = None

    for log_day in sorted(completed_dates):
        # Si el día actual es exactamente el día siguiente al previous,
        # seguimos la racha.
        if previous and log_day == previous + timedelta(days=1):
            running += 1
        else:
            # Si hay hueco, reinicia racha.
            running = 1

        best = max(best, running)
        previous = log_day

    return current, best


def habit_completion_rate(habit_id: int, days: int) -> float:
    """
    Calcula % de cumplimiento para un hábito en ventana de N días.

    Fórmula:
      completados_en_rango / days * 100

    Ej:
    - Si days=7 y completaste 5 días -> 5/7 * 100 = 71.4%

    Nota:
    - Tú ya proteges days=0 con "if days else 0.0"
      (igual clamp_range_days normalmente evita 0).
    """
    start_date = date.today() - timedelta(days=days - 1)

    # COUNT de logs completados del hábito desde start_date hasta hoy.
    completed = (
        db.session.query(func.count(HabitLog.id))
        .filter(
            HabitLog.habit_id == habit_id,
            HabitLog.completed.is_(True),
            HabitLog.log_date >= start_date,
        )
        .scalar()
    )

    return round((completed / days) * 100, 1) if days else 0.0


def global_completion_rate(user_id: int, days: int) -> float:
    """
    Calcula % global para hábitos activos del usuario.

    Tu definición:
    - Denominador = (#hábitos_activos) * (days)
    - Numerador = cantidad TOTAL de logs completados en ese periodo
      para los hábitos activos.

    Ej:
    - 3 hábitos activos, 7 días => denominador = 21 "oportunidades"
    - Si completaste 10 logs => 10/21 = 47.6%

    Importante:
    - Esto mide constancia TOTAL, no "días perfectos".
    - Está bien para un dashboard.
    """
    # Traemos ids de hábitos activos (solo Habit.id).
    active_habit_ids = [
        row.id
        for row in Habit.query.filter_by(user_id=user_id, is_active=True)
        .with_entities(Habit.id)
        .all()
    ]

    # Si no hay hábitos activos, no existe cumplimiento global.
    if not active_habit_ids:
        return 0.0

    start_date = date.today() - timedelta(days=days - 1)

    completed_total = (
        db.session.query(func.count(HabitLog.id))
        .filter(
            HabitLog.habit_id.in_(active_habit_ids),
            HabitLog.completed.is_(True),
            HabitLog.log_date >= start_date,
        )
        .scalar()
    )

    denominator = len(active_habit_ids) * days
    return round((completed_total / denominator) * 100, 1) if denominator else 0.0


def global_streaks(user_id: int) -> tuple[int, int]:
    """
    Calcula rachas globales agrupando por fecha para hábitos activos.

    ¿Qué significa "racha global" aquí?
    - Un día cuenta como "cumplido" si completaste AL MENOS 1 hábito activo ese día.
    - Por eso haces group_by(log_date): te quedas con fechas únicas.

    Luego:
    - conviertes esas fechas en set
    - y reutilizas calculate_streaks (buenísimo, DRY).
    """
    rows = (
        db.session.query(HabitLog.log_date)
        .join(Habit, Habit.id == HabitLog.habit_id)
        .filter(
            Habit.user_id == user_id,
            Habit.is_active.is_(True),
            HabitLog.completed.is_(True),
        )
        .group_by(HabitLog.log_date)
        .all()
    )

    # rows trae fechas únicas; convertimos a set de date y calculamos rachas
    return calculate_streaks({row.log_date for row in rows})


def summary_series_for_user(user_id: int, days: int) -> dict:
    """
    Construye datos del dashboard para:
    1) tendencia global: conteo de completados por día (últimos N días)
    2) barras por hábito: % de cumplimiento por hábito (mismo rango)

    Salida:
    {
      "series": {"labels": [...], "values": [...]},
      "habits": [{"name": "...", "value": 70.0}, ...]
    }
    """
    dates = date_series(days)
    labels = [d.isoformat() for d in dates]

    # IDs de hábitos activos (para contar completados globales solo de activos)
    active_habit_ids = [
        row.id
        for row in Habit.query.filter_by(user_id=user_id, is_active=True)
        .with_entities(Habit.id)
        .all()
    ]

    # Diccionario: fecha -> conteo de logs completados ese día
    counts_by_date = defaultdict(int)

    if active_habit_ids:
        # Traemos una tabla agregada:
        # (log_date, count)
        rows = (
            db.session.query(HabitLog.log_date, func.count(HabitLog.id))
            .filter(
                HabitLog.habit_id.in_(active_habit_ids),
                HabitLog.completed.is_(True),
                HabitLog.log_date >= dates[0],  # desde el primer día del rango
            )
            .group_by(HabitLog.log_date)
            .all()
        )

        # rows viene como tuplas (log_day, count).
        # Lo convertimos a dict y lo metemos en counts_by_date.
        counts_by_date.update({log_day: count for log_day, count in rows})

    # values: para cada día del rango, sacamos su conteo (0 si no existe)
    values = [counts_by_date[d] for d in dates]

    # Barras por hábito:
    # OJO: aquí incluyes TODOS los hábitos (activos e inactivos).
    # Si quieres que el "top" sea solo activos, filtra is_active=True.
    habits = (
        Habit.query
        .filter_by(user_id=user_id)
        .order_by(Habit.name.asc())
        .all()
    )

    habits_rates = [
        {"name": habit.name, "value": habit_completion_rate(habit.id, days)}
        for habit in habits
    ]

    return {
        "series": {"labels": labels, "values": values},
        "habits": habits_rates,
    }


def weekday_counts_for_user(user_id: int, days: int) -> dict:
    """
    Cuenta completados por día de la semana en una ventana de N días.

    ¿Para qué?
    - Para un gráfico "Lun..Dom" donde ves en qué días eres más consistente.

    Cómo funciona:
    - Traes todos los log_date completados en el rango
    - weekday() te da:
      Lun=0, Mar=1, ..., Dom=6
    - incrementas values[weekday]
    """
    start_date = date.today() - timedelta(days=days - 1)

    rows = (
        db.session.query(HabitLog.log_date)
        .join(Habit, Habit.id == HabitLog.habit_id)
        .filter(
            Habit.user_id == user_id,
            HabitLog.completed.is_(True),
            HabitLog.log_date >= start_date,
        )
        .all()
    )

    labels = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    values = [0] * 7

    # rows devuelve una lista de tuplas (log_date,), por eso (log_day,) desempaca.
    for (log_day,) in rows:
        values[log_day.weekday()] += 1

    return {"labels": labels, "values": values}