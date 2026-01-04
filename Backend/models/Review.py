from datetime import datetime
from database import db


class Review(db.Model):
  __tablename__ = "reviews"

  __table_args__ = (db.UniqueConstraint("booking_id", "reviewer_id", name="uq_review_booking_reviewer"),)

  id = db.Column(db.Integer, primary_key=True)
  booking_id = db.Column(db.Integer, db.ForeignKey("booking.id"), nullable=False, index=True)
  reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
  reviewed_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
  rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
  comment = db.Column(db.Text, nullable=True)

  created_at = db.Column(db.DateTime, default=datetime.utcnow)

  # Relationships
  booking = db.relationship("Booking", backref="reviews", lazy=True)
  reviewer = db.relationship("User", foreign_keys=[reviewer_id], backref="reviews_given", lazy=True)
  reviewed = db.relationship("User", foreign_keys=[reviewed_id], backref="reviews_received", lazy=True)

  def to_dict(self):
    return {"id": self.id, "booking_id": self.booking_id, "reviewer_id": self.reviewer_id,
      "reviewed_id": self.reviewed_id, "rating": self.rating, "comment": self.comment,
      "created_at": self.created_at.isoformat() if self.created_at else None,
      "reviewer": {"id": self.reviewer.id, "username": self.reviewer.username, "first_name": self.reviewer.first_name,
        "last_name": self.reviewer.last_name, } if self.reviewer else None, }

  def __repr__(self):
    return f"<Review id={self.id} booking_id={self.booking_id} rating={self.rating}>"
