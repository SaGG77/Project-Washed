from datetime import datetime
from extensions import db

class HabitLog(db.Model):
    __tablename__ = "habits_logs"

    id = db.Column(db.Integer, primary_key=True)

    habit_id = db.Column(db.Integer, db.ForeignKey("habits.id"), nullable=False, index=True)

    # Fecha del registro
    log_date = db.Column(db.Date, nullable=False, index=True)

    # Meta de minutos al dia
    completed = db.Column(db.Boolean, default=False, nullable=True)

    # Bandera para activar o desactivar hábito sin borrarlo
    minutes = db.Column(db.Integer, nullable=False)

    # Timestamp de creación
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("habit_id", "log_date", name="uq_habit_log_habit_date"),
    )
