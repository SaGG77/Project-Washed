from flask import Blueprint, render_template, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from forms import RegistroForm, LoginForm
from models.user import User
from utils.auth import login_required

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/perfil")
@login_required
def perfil():
    user_id = session.get("user_id")
    
    user = User.query.get(user_id)
    return render_template("auth/perfil.html", user=user)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegistroForm()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Correo ya registrado. Inicia sesión", "warning")
            return render_template("auth/login.html", form=form)

        nuevo = User(
            nombre=form.nombre.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.contraseña.data),
        )
        db.session.add(nuevo)
        db.session.commit()

        session["user_id"] = nuevo.id
        return redirect(url_for("auth.perfil"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.contraseña.data):
            session["user_id"] = user.id
            return redirect(url_for("auth.perfil"))

        flash("Alguno de tus datos fueron incorrectos", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))
