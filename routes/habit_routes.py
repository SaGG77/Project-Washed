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
# Form
from forms import HabitForm

habit_bp = Blueprint("habit", __name__)

@habit_bp.route("/habits/new", methods=["GET", "POST"])
@login_required
def create_habit():
    user_id = session.get("user_id")
    form = HabitForm()

    if form.validate_on_submit():
        habit = Habit(
            user_id=user_id,
            name=form.name.data.strip(),
            target_minutes=form.target_minutes.data,
            is_active=form.is_active.data,
        )
        db.session.add(Habit)
        db.session.commit()
        flash("Habito creado con exito", "success")
        return redirect(url_for("habits.habits"))
    return render_template("habits/new.html", form=form)


@habit_bp.route("/habits", methods=["GET"])
@login_required
def habits():
    user_id = session.get("user_id")

    habits = Habit.query.filter_by(user_id=user_id).order_by(Habit.created_at.desc()).all()

    return render_template("/habits/index.html", habits=habits)