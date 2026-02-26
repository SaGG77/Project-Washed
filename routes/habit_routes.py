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

@habit_bp.route("/index", methods=["GET"])
@login_required
def index():
    user_id = session.get("user_id")

    habits = Habit.query.filter_by(user_id=user_id).order_by(Habit.created_at.desc()).all()

    return render_template("/habits/index.html", habits=habits)

@habit_bp.route("/habits/new_habit", methods=["GET", "POST"])
@login_required
def new_habit():
    user_id = session.get("user_id")
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
        flash("Habito creado con exito", "success")
        return redirect(url_for("habit.index"))
    return render_template("habits/new.html", form=form)


""""
@habit_bp.route("/<int:item_id>/delete", methods=["POST"])
@login_required
def delete(item_id):
    user_id = session["user_id"]

    item = Habit.query.filter_by(id=item_id, user_id=user_id).first_or_404()

    db.session.delete(item)
    db.session.commit()

    flash("Registro eliminado", "success")
    return redirect(url_for("media.index"))
"""
@habit_bp.route("/<int:habit_id>/edit", methods=["GET", "POST"])
@login_required
def edit_habit(habit_id):
    user_id = session["user_id"]

    habit = Habit.query.filter_by(id=habit_id, user_id=user_id).first_or_404()
        #item
    form = HabitForm(obj=habit)

    if form.validate_on_submit():
        form.populate_obj(habit)
        habit.name = habit.name.strip()
        db.session.commit()
        flash("Habito actualizado correctamente", "success")
        return redirect(url_for("habits.index"))

    # GET: mostrar form relleno
    return render_template("media/edit.html", form=form, habit=habit)