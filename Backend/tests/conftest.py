import hashlib
import pytest
from flask import Flask
from flask_jwt_extended import JWTManager

from models.enums import UserRole
from blueprints.userAccess import user_access
from blueprints.Bookings import bookings
from blueprints.Rides import rides
from database import db
from models.User import User

@pytest.fixture()
def mock_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = "test_secret"
    jwt = JWTManager(app)
    # Initialize and register everything
    db.init_app(app)
    app.register_blueprint(user_access)
    app.register_blueprint(bookings)
    app.register_blueprint(rides)

    # Create and tear down database per test session
    with app.app_context():
        db.create_all()

        driver = User(
                    id=1,
                    username="driver",
                    email="driver@example.com",
                    password=hashlib.sha256(b"test").hexdigest(),
                    role=UserRole.DRIVER,
                    first_name="Driver",
                    last_name="User"
                )
        passenger = User(
            id=2,
            username="passenger",
            email="passenger@example.com",
            password=hashlib.sha256(b"test").hexdigest(),
            role=UserRole.DEFAULT,
            first_name="Passenger",
            last_name="User"
        )
        db.session.add_all([driver, passenger])
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(mock_app):
    """Provides a test client for making requests."""
    return mock_app.test_client()
