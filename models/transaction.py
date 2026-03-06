from datetime import datetime
from extensions import db

class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    type = db.Column(db.String(10), nullable=False, index=True)  # "income" | "expense"
    amount = db.Column(db.BigInteger, nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    notes = db.Column(db.Text)

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)