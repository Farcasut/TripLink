import hashlib
from datetime import timedelta

from flask import Blueprint, render_template, abort, request, jsonify
from jinja2 import TemplateNotFound
import re
from models.User import User
from CustomHttpException import CustomHttpException
from CustomHttpException import exception_raiser
from database import db
from flask_jwt_extended import create_access_token, current_user, get_jwt_identity

user_access = Blueprint("user_access", __name__)

email_regex = re.compile(r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$')


def is_email_valid(email: str) -> bool:
  if email_regex.match(email):
    return True
  else:
    return False


def user_exists(email: str, username: str) -> bool:
  return User.query.filter_by(email=email, username=username).first() is not None


@user_access.post("/register")
def register():
  try:
    data = request.get_json()
    data["password"] = hashlib.sha256(data["password"].encode()).hexdigest()
    user = User(**data)
    exception_raiser(not is_email_valid(user.email), "error", "Invalid email", 400)
    exception_raiser(user_exists(user.email, user.username), "error", "Email already exists", 400)
    user.role = 1
    db.session.add(user)
    db.session.commit()
    token = create_access_token(identity=user.get_identy(), expires_delta=timedelta(days=1))
    return jsonify({"status": "success", "message": "User registered", "content": token}), 201
  except CustomHttpException as e:
    return jsonify({'status': e.status, "message": str(e)}), e.status_code
  except Exception as e:
    db.session.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


@user_access.post("/login")
def login():
  try:
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    exception_raiser(username and password, "error", "Username and password required", 400)
    user = User.query.filter_by(username=username).first()
    exception_raiser(user is not None, "error", "Invalid username or password", 401)

    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    exception_raiser(user.password == hashed_password, "error", "Invalid username or password", 401)

    token = create_access_token(identity=user.get_identity(), expires_delta=timedelta(days=1))
    print(token)
    return 200



  except CustomHttpException as e:
    return jsonify({'status': e.status, "message": str(e)}), e.status_code
  except Exception as e:
    return jsonify({"status": "error", "message": str(e)}), 400
