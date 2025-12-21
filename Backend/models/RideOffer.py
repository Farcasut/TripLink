from database import db

ride_passengers = db.Table(
    "ride_passengers",
    db.Column("ride_id", db.Integer, db.ForeignKey("ride_offers.id"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True)
)

class RideOffer(db.Model):
    __tablename__ = "ride_offers"
    id: int = db.Column(db.Integer, primary_key=True)
    author_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    source: str = db.Column(db.String(120), nullable=False)
    destination: str = db.Column(db.String(120), nullable=False)
    departure_date: int = db.Column(db.Integer, nullable=False)
    ## Left for the UI to be able to grey out the expired rides whenever a driver/passenger looks at the history.
    ## To get all active rides you should filter after departure_date - 3600 > now.
    active: int = db.Column(db.Boolean, default=True, nullable=False)
    price: int = db.Column(db.Integer, nullable=False)
    available_seats: int = db.Column(db.Integer, nullable=False)
    passengers = db.relationship(
        "User",
        secondary=ride_passengers,
        backref=db.backref("rides_joined", lazy=True)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "author_id": self.author_id,
            "source": self.source,
            "destination": self.destination,
            "departure_date": self.departure_date,
            "active": self.active,
            "passenger_ids": [p.id for p in self.passengers]
        }
