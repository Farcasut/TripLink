from models.enums import UserRole
from database import db


class User(db.Model):
  __tablename__ = "user"
  id: int = db.Column(db.Integer, primary_key=True)
  role: int = db.Column(db.Integer, nullable=False,default=UserRole.DEFAULT)
  username: str = db.Column(db.String(16), unique=True, nullable=False,index=True)
  password: str = db.Column(db.String(120), nullable=False)
  email: str = db.Column(db.String(120), unique=True, nullable=False,index=True)
  last_name: str = db.Column(db.String(32), nullable=False)
  first_name: str = db.Column(db.String(32), nullable=False)
  bookings = db.relationship("Booking", backref="passenger", lazy=True, cascade="all, delete-orphan")

  def to_dict(self):
    return {
      "id": self.id,
      "username": self.username,
      "email": self.email,
      "last_name": self.last_name,
      "first_name": self.first_name,
      "role": self.role,
    }

  def is_driver(self) -> bool:
        return self.role == UserRole.DRIVER

  def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username}>"

  def get_identity(self) -> str:
    return str(self.id)

  def get_additional_claims(self) -> dict:
    return {
      "first_name": self.first_name,
      "last_name": self.last_name,
      "username": self.username,
      "role": self.role
    }
