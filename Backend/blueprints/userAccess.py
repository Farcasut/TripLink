import hashlib
from datetime import timedelta

from sqlalchemy import or_
from flask import Blueprint, render_template, abort, request, jsonify
from jinja2 import TemplateNotFound
import re

from blueprints.UserRoles import UserRoles
from models.User import User
from CustomHttpException import CustomHttpException
from CustomHttpException import exception_raiser
from database import db
from flask_jwt_extended import create_access_token, current_user, get_jwt_identity

user_access = Blueprint("user_access", __name__)

email_regex = re.compile(r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$')


def is_email_valid(email: str) -> bool:
  """
  Validate email format using a regex pattern.
  Args:
      email (str): The email address to validate.
  Returns:
      bool: True if the email is valid, False otherwise.
  """
  if email_regex.match(email):
    return True
  else:
    return False


def user_exists(email: str, username: str) -> bool:
  """
  Check whether a user with the given email or username already exists.
  Args:
      email (str): User's email address.
      username (str): User's username.
  Returns:
      bool: True if user exists, False otherwise.
  """
  return User.query.filter(
    or_(User.email == email, User.username == username)
  ).first() is not None


@user_access.post("/register")
def register():
  """
  Handle new user registration.

  Expects JSON payload:
      {
          "username": "string",
          "password": "string",
          "email": "string",
          "first_name": "string",
          "last_name": "string"
      }
  Steps:
  - Validate email format.
  - Ensure user does not already exist.
  - Hash the password
  - Save the new user
  - Generate a JWT valid for 1 day.

  Returns:
      JSON response with success status, message, and token.
      - 201, if the user was created
      - 400, if the email is invalid | email already exists | db exception
  """
  try:
    data = request.get_json()
    data["password"] = hashlib.sha256(data["password"].encode()).hexdigest()
    user: User = User(**data)
    exception_raiser(not is_email_valid(user.email), "error", "Invalid email", 400)
    exception_raiser(user_exists(user.email, user.username), "error", "Email already exists", 400)
    user.role = UserRoles.DEFAULT.value
    db.session.add(user)
    db.session.commit()
    token = create_access_token(identity=user.get_identity(), expires_delta=timedelta(days=1))
    return jsonify({"status": "success", "message": "User registered", "content": token}), 201
  except CustomHttpException as e:
    return jsonify({'status': e.status, "message": str(e)}), e.status_code
  except Exception as e:
    db.session.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@user_access.post("/login")
def login():
  """
  Handle user login and JWT token creation.

  Expects JSON payload:
      {
          "username": "string",
          "password": "string"
      }
  Steps:
  - Validate username and password are provided.
  - Verify username exists.
  - Compare hashed password with stored hash.
  - Generate a JWT valid for 1 day
  Returns:
      JSON response with status, message, and access token.
      - 400, if the username or the password is missing | db exception
      - 401, if the password or username is invalid
      - 200, if everything went ok
  """
  try:
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    exception_raiser(not (username and password), "error", "Username and password required", 400)
    user = User.query.filter_by(username=username).first()
    exception_raiser(user is None, "error", "Invalid username or password", 401)

    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    exception_raiser(user.password != hashed_password, "error", "Invalid username or password", 401)

    token = create_access_token(identity=user.get_identity(), expires_delta=timedelta(days=1))
    return jsonify({"status": "success", "message": "User logged", "content": token}), 200
  except CustomHttpException as e:
    return jsonify({'status': e.status, "message": str(e)}), e.status_code
  except Exception as e:
    return jsonify({"status": "error", "message": str(e)}), 400
