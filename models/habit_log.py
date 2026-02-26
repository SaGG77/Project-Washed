# datetime.utcnow para sello temporal de creación del log.
from datetime import datetime

# Instancia SQLAlchemy compartida.
from extensions import db


# Modelo de registro diario de hábitos.
# Cada fila corresponde a un hábito en una fecha específica.
class HabitLog(db.Model):
    # Nombre de tabla en DB.
    __tablename__ = "habit_logs"

    # Clave primaria autoincremental.
    id = db.Column(db.Integer, primary_key=True)

    # Relación al hábito padre.
    # index=True acelera consultas por hábito.
    habit_id = db.Column(db.Integer, db.ForeignKey("habits.id"), nullable=False, index=True)

    # Fecha del registro (sin hora).
    # index=True acelera filtros por rango de fechas.
    log_date = db.Column(db.Date, nullable=False, index=True)

    # Indica si el hábito fue completado ese día.
    completed = db.Column(db.Boolean, default=False, nullable=False)

    # Minutos dedicados ese día (opcional).
    minutes = db.Column(db.Integer, nullable=True)

    # Fecha/hora de creación del registro.
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Restricción de unicidad:
    # para un hábito dado no puede haber dos logs en la misma fecha.
    __table_args__ = (
        db.UniqueConstraint("habit_id", "log_date", name="uq_habit_log_habit_date"),
    )
