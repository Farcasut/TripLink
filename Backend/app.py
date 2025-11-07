import os
from typing import Final
from flask import Flask
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager

from database import db
import models.User
import argparse
from blueprints.userAccess import user_access

load_dotenv()


def create_app():
  app: Flask = Flask(__name__)
  postgres_user = os.getenv("POSTGRES_USER",)
  postgres_password = os.getenv("POSTGRES_PASSWORD")
  postgres_db_name = os.getenv("POSTGRES_DB")
  postgres_host = os.getenv("POSTGRES_HOST")
  postgres_port = os.getenv("POSTGRES_PORT")
  app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{postgres_user}:{postgres_password}"
    f"@{postgres_host}:{postgres_port}/{postgres_db_name}"
  )
  app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET")
  app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
  app.register_blueprint(user_access)
  jwt = JWTManager(app)
  return app


def setup_db(app: Flask, reset_db: bool = False):
  db.init_app(app)

  with app.app_context():
    if reset_db:
      print("Dropped all tables.")
      db.drop_all()
    db.create_all()
    print("Created all tables.")


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Run the Flask app.")
  parser.add_argument("--reset-db", action="store_true", help="Drop and recreate all tables.")
  args = parser.parse_args()

  app = create_app()
  setup_db(app, args.reset_db)
  print("Registered tables:", db.Model.metadata.tables.keys())
  app.run(host=os.getenv("host"), port=int(os.getenv("port")), debug=True)
