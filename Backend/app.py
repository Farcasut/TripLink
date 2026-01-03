import os
from flask import Flask
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from sqlalchemy import text
from database import db
import argparse

from blueprints.UserProfile import user_profile
from blueprints.Cities import cities
from blueprints.Rides import rides
from blueprints.Bookings import bookings
from blueprints.DriverAccess import driver_access
from blueprints.userAccess import user_access
from blueprints import ChatService
import FetchCities

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

    # TODO(fix): solve CSRF.
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET")
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    app.config['JWT_COOKIE_SECURE'] = False
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.register_blueprint(user_access)
    app.register_blueprint(driver_access)
    app.register_blueprint(cities)
    app.register_blueprint(rides)
    app.register_blueprint(bookings)
    app.register_blueprint(user_profile)
    app.register_blueprint(ChatService.chat_route)
    jwt = JWTManager(app)
    return app

def setup_db(app: Flask, reset_db: bool = False):
    db.init_app(app)

    with app.app_context():
        if reset_db:
            print("Dropped all tables.")
            with db.engine.begin() as conn:
                conn.execute(text("DROP SCHEMA public CASCADE"))
                conn.execute(text("CREATE SCHEMA public"))

        db.create_all()
        print("Created all tables.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Flask app.")
    parser.add_argument("--reset-db", action="store_true", help="Drop and recreate all tables.")
    args = parser.parse_args()

    app = create_app()
    setup_db(app, args.reset_db)
    print("Registered tables:", db.Model.metadata.tables.keys())
    FetchCities.prefetch('romania')
    ChatService.preload()
    app.run(host=os.getenv("host"), port=int(os.getenv("port")), debug=True, use_reloader=False)
