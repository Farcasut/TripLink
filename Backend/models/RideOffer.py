from database import db

ride_passengers = db.Table(
  "ride_passengers",
  db.Column("ride_id", db.Integer, db.ForeignKey("ride_offer.id"), primary_key=True),
  db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True)
)

class RideOffer(db.Model):
  __tablename__ = "ride_offer"
  id: int = db.Column(db.Integer, primary_key=True)
  author_id: int = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False,index=True)
  source: str = db.Column(db.String(120), nullable=False)
  destination: str = db.Column(db.String(120), nullable=False)
  departure_date: int = db.Column(db.Integer, nullable=False,index=True)
  ## Left for the UI to be able to grey out the expired rides whenever a driver/passenger looks at the history.
  ## To get all active rides you should filter after departure_date - 3600 > now.
  active: bool = db.Column(db.Boolean, default=True, nullable=False)
  price: int = db.Column(db.Integer, nullable=False)
  available_seats: int = db.Column(db.Integer, nullable=False)
  author = db.relationship("User", backref=db.backref("rides_created", lazy=True))
  bookings = db.relationship("Booking", backref="ride", lazy=True, cascade="all, delete-orphan")

  def to_dict(self):
      return {
          "id": self.id,
          "author_id": self.author_id,
          "source": self.source,
          "destination": self.destination,
          "departure_date": self.departure_date,
          "price": self.price,
          "available_seats": self.available_seats,
          "active": self.active,
      }

