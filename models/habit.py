# datetime.utcnow nos sirve para timestamps de creación/actualización.
from datetime import datetime

# db es la instancia de SQLAlchemy definida en extensions.py.
from extensions import db


# Modelo principal de hábitos.
# Cada fila representa un hábito configurable por usuario.
class Habit(db.Model):
    # Nombre real de tabla en la base de datos.
    __tablename__ = "habits"

    # ID autoincremental, clave primaria.
    id = db.Column(db.Integer, primary_key=True)

    # Dueño del hábito (relación hacia users.id).
    # index=True acelera búsquedas por usuario.
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # Nombre del hábito (ej: "Leer", "Entrenar").
    name = db.Column(db.String(120), nullable=False)

    # Meta opcional en minutos por día.
    target_minutes = db.Column(db.Integer, nullable=True)

    # Bandera para activar/desactivar hábito sin borrarlo.
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Timestamp de creación.
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Timestamp de actualización (se auto-actualiza al modificar la fila).
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relación 1:N con HabitLog.
    # - backref="habit": permite usar log.habit
    # - cascade="all, delete-orphan": si se borra el hábito, borra sus logs
    # - lazy=True: carga la colección al acceder (carga diferida)
    logs = db.relationship(
        "HabitLog",
        backref="habit",
        cascade="all, delete-orphan",
        lazy=True,
    )
