from Backend.database import db

class Driver(db.Model):
    __tablename__ = "driver"

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)

    driver_license_number: str = db.Column(db.String(32), unique=True, nullable=False)
    driver_license_expiry_date: str = db.Column(db.String(20), nullable=False)

    vehicle_brand: str = db.Column(db.String(64), nullable=False)
    vehicle_model: str = db.Column(db.String(64), nullable=False)
    vehicle_year: int = db.Column(db.Integer, nullable=False)
    license_plate_number: str = db.Column(db.String(32), nullable=False)
    vehicle_color: str = db.Column(db.String(32), nullable=False)
    number_of_seats: int = db.Column(db.Integer, nullable=False)

    bank_account_holder_name: str = db.Column(db.String(128), nullable=False)
    bank_account_number: str = db.Column(db.String(64), nullable=False)
    bank_name: str = db.Column(db.String(64), nullable=False)
    payment_method_preference: str = db.Column(db.String(64), nullable=False)

    user = db.relationship("User", backref=db.backref("driver_profile", uselist=False))

    def __repr__(self):
        return f"<Driver id={self.id} user_id={self.user_id} license={self.driver_license_number}>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "driver_license_number": self.driver_license_number,
            "driver_license_expiry_date": self.driver_license_expiry_date,
            "vehicle_brand": self.vehicle_brand,
            "vehicle_model": self.vehicle_model,
            "vehicle_year": self.vehicle_year,
            "license_plate_number": self.license_plate_number,
            "vehicle_color": self.vehicle_color,
            "number_of_seats": self.number_of_seats,
            "bank_account_holder_name": self.bank_account_holder_name,
            "bank_account_number": self.bank_account_number,
            "bank_name": self.bank_name,
            "payment_method_preference": self.payment_method_preference,
        }