from database import db

class User(db.Model):

  __tablename__ = "users"
  id:int = db.Column(db.Integer, primary_key=True)
  username:str = db.Column(db.String(16), unique=True, nullable=False)
  email:str = db.Column(db.String(120), unique=True, nullable=False)
  last_name: str = db.Column(db.String(32), unique=True, nullable=False)
  first_name: str = db.Column(db.String(32), unique=True, nullable=False)


  def to_dict(self):
    return {
      "id" : self.id,
      "username": self.username,
      "email": self.email,
      "last_name": self.last_name,
      "first_name": self.first_name
    }

  def __repr__(self):
    return f"<User {self.username}>"
