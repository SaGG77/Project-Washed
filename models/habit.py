from datetime import datetime
from extensions import db

class Habit(db.Model):
    __tablename__ = "habits"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # Nombre de la actividad
    name = db.Column(db.String(120), nullable=False)

    # Meta de minutos al dia
    target_minutes = db.Column(db.Integer, nullable=True)

    # Bandera para activar o desactivar hábito sin borrarlo
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Timestamp de creación
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Timestamp de actualización
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


    logs = db.relationship(
        "HabitLog",
        backref="habit",
        cascade="all, delete-orphan",
        lazy=True,
    )