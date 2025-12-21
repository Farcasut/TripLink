import hashlib
from datetime import timedelta

from sqlalchemy import or_
from flask import Blueprint, render_template, abort, request, jsonify, redirect, make_response
from jinja2 import TemplateNotFound
import re

from models.User import User
from blueprints.userAccess import is_password_strong
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

user_profile = Blueprint("user_profile", __name__)

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

@user_profile.route("/profile", methods=["GET", "POST"], strict_slashes=False)
@jwt_noapi_required
def profile():
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

            # Handle password change
            current_password = data.get("current_password")
            new_password = data.get("password")
            confirm_password = data.get("confirm_password")
            
            # If user wants to change password
            if new_password or confirm_password or current_password:
                # All three fields must be provided
                exception_raiser(
                    not current_password, 
                    "error", 
                    "Current password is required to change password", 
                    400
                )
                exception_raiser(
                    not new_password, 
                    "error", 
                    "New password is required", 
                    400
                )
                exception_raiser(
                    not confirm_password, 
                    "error", 
                    "Password confirmation is required", 
                    400
                )
                
                # Verify current password
                hashed_current = hashlib.sha256(current_password.encode()).hexdigest()
                exception_raiser(
                    user.password != hashed_current,
                    "error",
                    "Current password is incorrect",
                    401
                )
                
                # Check if new passwords match
                exception_raiser(
                    new_password != confirm_password,
                    "error",
                    "New passwords do not match",
                    400
                )
                
                # Check if new password is different from current
                exception_raiser(
                    new_password == current_password,
                    "error",
                    "New password must be different from current password",
                    400
                )

                exception_raiser(not is_password_strong(new_password)[0], 'error', 'New password is too weak.', 400)
                
                # Update password
                user.password = hashlib.sha256(new_password.encode()).hexdigest()
            
            # Validate email format
            exception_raiser(not is_email_valid(user.email), "error", "Invalid email format.", 400)
            
            # Check if email already exists (excluding current user)
            existing_user = User.query.filter(
                User.email == user.email, 
                User.id != user.id
            ).first()
            exception_raiser(existing_user is not None, "error", "Email already exists.", 400)
            
            db.session.commit()
            token = create_access_token(identity=user.get_identity(), additional_claims=user.get_additional_claims(), expires_delta=timedelta(days=1))
            response = make_response(render_template('profile.html', 
                                 user=user, 
                                 message="Profile updated successfully!",
                                 message_type="success"))

            set_access_cookies(response, token)
            return response
                                 
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
    
    # Show profile form
    try:
        return render_template('profile.html', user=user)
    except TemplateNotFound:
        abort(404)
