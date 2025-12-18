from datetime import datetime
from database import db

class Booking(db.Model):
    __tablename__ = "booking"

    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(
        db.Integer,
        db.ForeignKey("ride_offer.id"),
        nullable=False
    )
    passenger_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    status = db.Column(
        db.String(16),
        nullable=False,
        default="pending"
    )
    # pending | accepted | denied

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

