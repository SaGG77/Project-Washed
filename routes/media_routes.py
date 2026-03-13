# LIBRERIAS
from flask import Blueprint, render_template, session, request, flash, redirect, url_for
from decimal import Decimal
from datetime import datetime
# PROPIO
from utils.auth import login_required
from forms import MediaForm
# BASES DE DATOS
from models.media_item import MediaItem
from extensions import db
#Ted, eres especial, pudsite ser una inspiracion para el mundo , ser un lider, un ejemplo a seguir, y un lugar de eso eres
media_bp = Blueprint("media", __name__, url_prefix="/media")

@media_bp.route("/")
@login_required
def index():
    user_id = session["user_id"]
    items = MediaItem.query.filter_by(user_id=user_id).all()
    return render_template("media/index.html", items=items)

@media_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = MediaForm()

    if form.validate_on_submit():
        user_id = session["user_id"]

        item = MediaItem(
            user_id=user_id,
            title=form.title.data.strip(),
            media_type=form.media_type.data,
            status=form.status.data,
            rating=float(form.rating.data) if form.rating.data is not None else None,
            tags=(form.tags.data or "").strip() or None,
            notes=(form.notes.data or "").strip() or None,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
        )

        db.session.add(item)
        db.session.commit()

        flash("Registro creado correctamente", "success")
        return redirect(url_for("media.index"))

    if request.method == "POST":
        flash("Revisa el formulario, hay campos inválidos", "warning")

    return render_template("media/new.html", form=form)

@media_bp.route("/<int:item_id>/delete", methods=["POST"])
@login_required
def delete(item_id):
    user_id = session["user_id"]

    item = MediaItem.query.filter_by(id=item_id, user_id=user_id).first_or_404()

    db.session.delete(item)
    db.session.commit()

    flash("Registro eliminado", "success")
    return redirect(url_for("media.index"))

@media_bp.route("/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit(item_id):
    user_id = session["user_id"]
    item = MediaItem.query.filter_by(id=item_id, user_id=user_id).first_or_404()

    form = MediaForm(obj=item)  # 👈 precarga con lo que ya existe

    if form.validate_on_submit():
        item.title = form.title.data.strip()
        item.media_type = form.media_type.data
        item.status = form.status.data
        item.rating = float(form.rating.data) if form.rating.data is not None else None
        item.tags = (form.tags.data or "").strip() or None
        item.notes = (form.notes.data or "").strip() or None
        item.start_date = form.start_date.data
        item.end_date = form.end_date.data

        db.session.commit()
        flash("Registro actualizado", "success")
        return redirect(url_for("media.index"))

    if request.method == "POST":
        flash("Revisa el formulario, hay campos inválidos", "warning")

    return render_template("media/edit.html", form=form, item=item)