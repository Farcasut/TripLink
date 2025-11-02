from flask import Blueprint, render_template, abort, request, jsonify
from jinja2 import TemplateNotFound
import re
from models.User import User
from CustomHttpException import CustomHttpException
from CustomHttpException import exception_raiser
from database import  db

user_access = Blueprint("user_access", __name__)

email_regex = re.compile(r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$')

def is_email_valid(email:str) -> bool:
  if email_regex.match(email):
    return True
  else:
    return False

def user_exists(email: str) -> bool:
  return User.query.filter_by(email = email).first() is not None

@user_access.post("register")
def register():
  try:
    data = request.get_json()
    user = User(**data)
    exception_raiser(is_email_valid(user.email), "error", "Invalid email", 400)
    exception_raiser(user_exists(user.email), "error", "Email already exists", 400)

  except CustomHttpException as e:
    return jsonify({'status': e.status, "message": str(e)}), e.status_code
  except Exception as e:
    db.session.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400


# @user_access.post("/login", )
# def login():
