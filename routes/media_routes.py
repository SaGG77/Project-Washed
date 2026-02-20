# LIBRERIAS
from flask import Blueprint, render_template, session, request, flash, redirect, url_for
from decimal import Decimal
from datetime import datetime
# PROPIO
from utils.auth import login_required
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
    if request.method == "POST":
        user_id = session["user_id"]

        title = request.form.get("title","").strip()
        media_type = request.form.get("media_type","").strip()
        notes = request.form.get("notes","").strip()
        status = request.form.get("status","").strip()
        rating_raw = request.form.get("rating","").strip()
        tags = request.form.get("tags ","").strip() or None
        start_date_raw = request.form.get("start_date","").strip()
        end_date_raw = request.form.get("end_date","").strip()

        if not title or not media_type or not rating_raw:
            flash("Titulo y tipo son obligatorios", "warning")
            return redirect(url_for("media.new", form_data=request.form))
        
        rating = None
        if rating_raw:
            try:
                rating = Decimal(rating_raw)
            except:
                flash("La calificacion debe ser un número (ej: 3.5)")
                return redirect(url_for("media.new", form_data=request.form))
        
        if rating < 0 or rating > 10:
            flash("La calificación debe estar entre 0 y 10.", "warning")
            return redirect(url_for("media.new", form_data=request.form))

        start_date = None
        end_date = None

        if start_date_raw:
            start_date = datetime.strptime(start_date_raw, "%Y-%m-%d").date()
        if end_date_raw:
            end_date = datetime.strptime(end_date_raw, "%Y-%m-%d").date()

        if start_date and end_date and end_date < start_date:
            flash("La fecha fin no puede ser anterior a la fecha de inicio.", "warning")
            return redirect(url_for("media.new", form_data=request.form))

        item = MediaItem(
            user_id=user_id,
            title=title,
            media_type=media_type,
            status=status,
            rating=rating,
            tags=tags,
            notes=notes,
            start_date=start_date,
            end_date=end_date
            
        )
        db.session.add(item)
        db.session.commit()

        flash("Creado", "success")
        return redirect(url_for("media.index"))

    return render_template("media/new.html")

@media_bp.route("/<int:item_id>/delete", methods=["POST"])
@login_required
def delete(item_id):
    user_id = session["user_id"]

    item = MediaItem.query.filter_by(id=item_id, user_id=user_id).first_or_404()

    db.session.delete(item)
    db.session.commit()

    flash("Registro eliminado", "success")
    return redirect(url_for("media.index"))