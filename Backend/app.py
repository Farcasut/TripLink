import os
import sys
from typing import Final
from flask import Flask
from dotenv import load_dotenv
from database import db
import models.User
import argparse

load_dotenv()



def create_app():
  app: Final[Flask] = Flask(__name__)
  postgres_user = os.getenv("POSTGRES_USER", "admin")
  postgres_password = os.getenv("POSTGRES_PASSWORD", "password")
  postgres_db_name = os.getenv("POSTGRES_DB", "tripLinkDB")
  postgres_host = os.getenv("POSTGRES_HOST", "localhost")
  postgres_port = os.getenv("POSTGRES_PORT", "5432")
  app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{postgres_user}:{postgres_password}"
    f"@{postgres_host}:{postgres_port}/{postgres_db_name}"
  )
  app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
  return  app

def setup_db(app: Final[Flask], reset_db: bool = False):
    db.init_app(app)
    with app.app_context():
        if reset_db:
            db.drop_all()
            print("Dropped all tables.")
        db.create_all()
        print("Created all tables.")

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Run the Flask app.")
  parser.add_argument("--reset-db", action="store_true", help="Drop and recreate all tables.")
  args = parser.parse_args()

  app = create_app()
  setup_db(app)
  print("Registered tables:", db.Model.metadata.tables.keys())
  app.run(host="0.0.0.0", port=5000, debug=True)
