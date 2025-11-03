import pytest
from flask import Flask
from flask_jwt_extended import JWTManager

from blueprints.userAccess import user_access
from database import db

@pytest.fixture()
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = "test_secret"
    jwt = JWTManager(app)
    # Initialize and register everything
    db.init_app(app)
    app.register_blueprint(user_access)

    # Create and tear down database per test session
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture()
def client(app):
    """Provides a test client for making requests."""
    return app.test_client()
