import hashlib
from datetime import timedelta

from sqlalchemy import or_
from flask import Blueprint, render_template, abort, request, jsonify, redirect
from jinja2 import TemplateNotFound
import jwt
import re

from blueprints.UserRoles import UserRoles
from models.User import User
from CustomHttpException import CustomHttpException
from CustomHttpException import exception_raiser
from CustomJWTRequired import jwt_noapi_required
from database import db
from flask_jwt_extended import (
    create_access_token, get_jwt_identity,
    jwt_required, verify_jwt_in_request,
    set_access_cookies, unset_jwt_cookies,
    get_csrf_token
)

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
    return jsonify({"status": "success", "message": "User registered"}), 201
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
    token = create_access_token(identity=str(user.id), expires_delta=timedelta(days=1))
    response = jsonify({"status": "success", "message": "User logged", "content": token})
    set_access_cookies(response, token)
    return response, 200
  except CustomHttpException as e:
    return jsonify({'status': e.status, "message": str(e)}), e.status_code
  except Exception as e:
    return jsonify({"status": "error", "message": str(e)}), 400

@user_access.get("/login")
def login_page():
    '''
      Simple login page form.
    '''

    try:
        return render_template('login.html')
    except TemplateNotFound:
        abort(404)

@user_access.get("/register")
def register_page():
    '''
      Simple register page form.
    '''
    
    try:
        return render_template('register.html')
    except TemplateNotFound:
        abort(404)

@user_access.route("/")
def user_index():
    '''
      Index router.
    '''
    
    try:
        verify_jwt_in_request()
        return redirect("/dashboard")
    except:
        return redirect("/login")

@user_access.route("/dashboard")
@jwt_noapi_required
def user_dashboard():
    '''
      Dashboard page.
    '''

    user_id = get_jwt_identity()
    user: User = User.query.get(int(user_id))
    
    try:
        return render_template('dashboard.html', user = user)
    except TemplateNotFound:
        abort(404)

@user_access.route('/logout')
@jwt_noapi_required
def user_logout():
    response = redirect("/login")
    unset_jwt_cookies(response)
    return response

@user_access.route("/profile", methods=["GET", "POST"])
@jwt_noapi_required
def user_profile():
    """
    User profile page and update functionality.
    """
    user_id = get_jwt_identity()
    user: User = User.query.get(int(user_id))
    
    if request.method == "POST":
        try:
            data = request.form
            
            # Update user fields
            user.first_name = data.get("first_name", user.first_name)
            user.last_name = data.get("last_name", user.last_name)
            user.email = data.get("email", user.email)
            
            # If password is provided, hash and update it
            new_password = data.get("password")
            if new_password:
                user.password = hashlib.sha256(new_password.encode()).hexdigest()
            
            # Validate email format
            exception_raiser(not is_email_valid(user.email), "error", "Invalid email format", 400)
            
            # Check if email already exists (excluding current user)
            existing_user = User.query.filter(
                User.email == user.email, 
                User.id != user.id
            ).first()
            exception_raiser(existing_user is not None, "error", "Email already exists", 400)
            
            db.session.commit()
            
            return render_template('profile.html', 
                                 user=user, 
                                 message="Profile updated successfully!",
                                 message_type="success")
                                 
        except CustomHttpException as e:
            db.session.rollback()
            return render_template('profile.html', 
                                 user=user, 
                                 message=str(e),
                                 message_type="error")
        except Exception as e:
            db.session.rollback()
            return render_template('profile.html', 
                                 user=user, 
                                 message="An error occurred while updating profile",
                                 message_type="error")
    
    # GET request - show profile form
    try:
        return render_template('profile.html', user=user)
    except TemplateNotFound:
        abort(404)