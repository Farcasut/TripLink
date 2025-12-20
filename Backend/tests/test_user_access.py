import hashlib

import pytest

from blueprints.UserRoles import UserRoles
from models.User import User
from database import db

def hash_pw(password: str) -> str:
    """Helper to hash passwords for test setup."""
    return hashlib.sha256(password.encode()).hexdigest()


# -----------------
# Register tests
# -----------------

@pytest.mark.order(1)
def test_register_success(client, mock_app):
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "mypassword", # FIX: Password validation.
        "first_name": "Test",
        "last_name": "User",
        "role": UserRoles.DEFAULT.value
    }
    response = client.post("/register", json=data)
    assert response.status_code == 201

    body = response.get_json()
    assert body["status"] == "success"
    # assert "content" in body # token is not present anymore

    with mock_app.app_context():
        user = User.query.filter_by(username="testuser").first()
        assert user is not None
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.role == UserRoles.DEFAULT.value

@pytest.mark.order(2)
def test_register_invalid_email(client):
    data = {
        "username": "bademail",
        "email": "invalidemail",
        "password": "pw", # FIX: Password validation.
        "first_name": "Bad",
        "last_name": "Email",
        "role": UserRoles.DEFAULT.value
    }

    response = client.post("/register", json=data)
    body = response.get_json()

    assert response.status_code == 400
    assert body["status"] == "error"
    assert "Invalid email" in body["message"]

@pytest.mark.order(3)
def test_register_duplicate_user(client, mock_app):
    # Add user directly to DB first
    with mock_app.app_context():
        user: User = User(
            username="duplicate",
            email="dup@example.com",
            password=hash_pw("pw"), # FIX: Password validation.
            role=UserRoles.DEFAULT.value,
            first_name="Dup",
            last_name="User"
        )
        db.session.add(user)
        db.session.commit()

    # Try registering again with same email
    data = {
        "username": "newuser",
        "email": "dup@example.com",
        "password": "pw", # FIX: Password validation.
        "first_name": "New",
        "last_name": "User",
        "role": 1
    }
    response = client.post("/register", json=data)
    body = response.get_json()

    assert response.status_code == 400
    assert 'message' in body
    assert body['message'] == 'User already exists.'
    assert 'content' in body
    assert "Email already exists." in body["content"]


# -----------------
# Login tests
# -----------------
@pytest.mark.order(4)
def test_login_success(client, mock_app):
    with mock_app.app_context():
        user: User = User(
            username="loginuser",
            email="login@example.com",
            password=hash_pw("secret"), # FIX: Password validation.
            role=UserRoles.DEFAULT.value,
            first_name="Login",
            last_name="User"
        )
        db.session.add(user)
        db.session.commit()

    data = {"username": "loginuser", "password": "secret"} # FIX: Password validation.
    response = client.post("/login", json=data)

    assert response.status_code == 200

@pytest.mark.order(5)
def test_login_wrong_password(client, mock_app):
    with mock_app.app_context():
        user: User = User(
            username="wrongpw",
            email="wrong@example.com",
            password=hash_pw("rightpassword"), # FIX: Password validation.
            role=UserRoles.DEFAULT.value,
            first_name="Wrong",
            last_name="Password"
        )
        db.session.add(user)
        db.session.commit()

    data = {"username": "wrongpw", "password": "incorrect"}
    response = client.post("/login", json=data)
    body = response.get_json()

    assert response.status_code == 401
    assert "Invalid username or password" in body["message"]

@pytest.mark.order(6)
def test_login_user_not_found(client):
    data = {"username": "ghost", "password": "12345"}
    response = client.post("/login", json=data)
    body = response.get_json()

    assert response.status_code == 401
    assert "Invalid username or password" in body["message"]
