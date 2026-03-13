from datetime import date, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from sqlalchemy import func

from extensions import db
from utils.auth import login_required

from models.category import Category
from models.transaction import Transaction

from forms import CategoryForm, TransactionForm
from utils.money import parse_cop_to_int, format_cop


finance_bp = Blueprint("finance", __name__)


# -------------------------
# DASHBOARD
# -------------------------
@finance_bp.route("/finance")
@login_required
def dashboard():
    user_id = session["user_id"]

    # rango: últimos 30 días (puedes cambiarlo luego)
    start = date.today() - timedelta(days=29)

    # Totales últimos 30 días
    income_total = (
        db.session.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(Transaction.user_id == user_id, Transaction.type == "income", Transaction.date >= start)
        .scalar()
    )
    expense_total = (
        db.session.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(Transaction.user_id == user_id, Transaction.type == "expense", Transaction.date >= start)
        .scalar()
    )

    balance = int(income_total) - int(expense_total)

    # Últimas 10 transacciones
    last_transactions = (
        Transaction.query
        .filter_by(user_id=user_id)
        .order_by(Transaction.date.desc(), Transaction.id.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "finance/dashboard.html",
        income_total=format_cop(int(income_total)),
        expense_total=format_cop(int(expense_total)),
        balance=format_cop(balance),
        last_transactions=last_transactions,
        format_cop=format_cop,
    )


# -------------------------
# LISTADO / HISTORIAL
# -------------------------
@finance_bp.route("/finance/transactions")
@login_required
def transactions_index():
    user_id = session["user_id"]

    q_type = request.args.get("type", "").strip()          # income/expense o vacío
    q_category = request.args.get("category_id", "").strip()  # id o vacío

    query = Transaction.query.filter_by(user_id=user_id)

    if q_type in ("income", "expense"):
        query = query.filter(Transaction.type == q_type)

    if q_category.isdigit():
        query = query.filter(Transaction.category_id == int(q_category))

    transactions = query.order_by(Transaction.date.desc(), Transaction.id.desc()).all()

    categories = (
        Category.query.filter_by(user_id=user_id)
        .order_by(Category.kind.asc(), Category.name.asc())
        .all()
    )
    categories_map = {c.id: c for c in categories}

    return render_template(
        "finance/index.html",
        transactions=transactions,
        categories=categories,
        categories_map=categories_map,
        format_cop=format_cop,
        q_type=q_type,
        q_category=q_category,
    )


# -------------------------
# CREAR TRANSACCIÓN
# -------------------------
@finance_bp.route("/finance/new", methods=["GET", "POST"])
@login_required
def transaction_new():
    user_id = session["user_id"]
    form = TransactionForm()

    # Llenar dropdown de categorías (solo del usuario).
    # Si quieres filtrar por tipo, más abajo te dejo el upgrade.
    categories = (
        Category.query.filter_by(user_id=user_id)
        .order_by(Category.kind.asc(), Category.name.asc())
        .all()
    )
    form.category_id.choices = [(c.id, f"{c.name} ({c.kind})") for c in categories]

    if not categories:
        flash("Primero crea una categoría para poder registrar transacciones.", "warning")
        return redirect(url_for("finance.categories_new"))

    if form.validate_on_submit():
        try:
            amount_int = parse_cop_to_int(form.amount.data)
        except ValueError:
            flash("Monto inválido. Ejemplo válido: 1.234.567", "danger")
            return render_template("finance/new.html", form=form)

        tx = Transaction(
            user_id=user_id,
            type=form.type.data,
            amount=amount_int,
            date=form.date.data,
            notes=form.notes.data.strip() if form.notes.data else None,
            category_id=form.category_id.data,
        )
        db.session.add(tx)
        db.session.commit()

        flash("Transacción guardada.", "success")
        return redirect(url_for("finance.transactions_index"))

    return render_template("finance/new.html", form=form)


# -------------------------
# CATEGORÍAS (CRUD)
# -------------------------
@finance_bp.route("/finance/categories")
@login_required
def categories_index():
    user_id = session["user_id"]
    categories = Category.query.filter_by(user_id=user_id).order_by(Category.kind.asc(), Category.name.asc()).all()
    return render_template("finance/categories/index.html", categories=categories)


@finance_bp.route("/finance/categories/new", methods=["GET", "POST"])
@login_required
def categories_new():
    user_id = session["user_id"]
    form = CategoryForm()

    if form.validate_on_submit():
        name = form.name.data.strip()
        kind = form.kind.data

        exists = Category.query.filter_by(user_id=user_id, name=name).first()
        if exists:
            flash("Ya existe una categoría con ese nombre.", "warning")
            return redirect(url_for("finance.categories_new"))

        db.session.add(Category(user_id=user_id, name=name, kind=kind))
        db.session.commit()

        flash("Categoría creada.", "success")
        return redirect(url_for("finance.categories.index"))

    return render_template("finance/categories/new.html", form=form)


@finance_bp.route("/finance/categories/<int:category_id>/edit", methods=["GET", "POST"])
@login_required
def categories_edit(category_id):
    user_id = session["user_id"]
    category = Category.query.filter_by(id=category_id, user_id=user_id).first_or_404()
    form = CategoryForm(obj=category)

    if form.validate_on_submit():
        category.name = form.name.data.strip()
        category.kind = form.kind.data
        db.session.commit()

        flash("Categoría actualizada.", "success")
        return redirect(url_for("finance.categories_index"))

    return render_template("finance/categories/edit.html", form=form, category=category)


@finance_bp.route("/finance/categories/<int:category_id>/delete", methods=["POST"])
@login_required
def categories_delete(category_id):
    user_id = session["user_id"]
    category = Category.query.filter_by(id=category_id, user_id=user_id).first_or_404()

    in_use = Transaction.query.filter_by(user_id=user_id, category_id=category.id).first()
    if in_use:
        flash("No puedes borrar esta categoría porque ya tiene transacciones.", "warning")
        return redirect(url_for("finance.categories.index"))

    db.session.delete(category)
    db.session.commit()
    flash("Categoría eliminada.", "success")
    return redirect(url_for("finance.categories.index"))