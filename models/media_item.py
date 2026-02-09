from datetime import datetime
from extensions import db
from sqlalchemy import Numeric

class MediaItem(db.Model):
    __tablename__ = "media_items"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, index=True)

    media_type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False)

    
    rating = db.Column(Numeric(3, 1), nullable=True)
    tags = db.Column(db.String(40), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


