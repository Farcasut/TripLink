from datetime import datetime
from database import db
from models.enums import BookingStatus

class Booking(db.Model):
    __tablename__ = "booking"

    __table_args__ = (
        db.UniqueConstraint(
            "ride_id",
            "passenger_id",
            name="uq_booking_ride_passenger"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey("ride_offer.id"), nullable=False, index=True)
    passenger_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    status = db.Column(db.String(16), nullable=False, default=BookingStatus.PENDING, index=True)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

