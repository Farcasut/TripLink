from datetime import timedelta

from flask import Blueprint, request, jsonify, render_template, abort
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, set_access_cookies
from database import db
from jinja2 import TemplateNotFound
from models.Driver import Driver
from models.User import User
from models.enums import UserRole
from CustomHttpException import exception_raiser, CustomHttpException

driver_access = Blueprint("driver_access", __name__, url_prefix="/driver")

@driver_access.route("/becomeDriver", methods=["GET", "POST"], strict_slashes=False)
@jwt_required()
def become_driver():
    """
    Allows a logged-in passenger to become a driver.
    Expects JSON:
    {
        "driver_license_number": "string",
        "driver_license_expiry_date": "string",
        "vehicle_brand": "string",
        "vehicle_model": "string",
        "vehicle_year": int,
        "license_plate_number": "string",
        "vehicle_color": "string",
        "number_of_seats": int,
        "bank_account_holder_name": "string",
        "bank_account_number": "string",
        "bank_name": "string",
        "payment_method_preference": "string"
    }
    """
    if request.method == "POST":
        try:
            user_id = int(get_jwt_identity())
            user = User.query.get(user_id)
            exception_raiser(user is None, "error", "User not found", 404)

            # Prevent duplicate driver profile
            existing_driver = Driver.query.filter_by(user_id=user_id).first()
            exception_raiser(existing_driver is not None, "error", "Already registered as driver", 400)

            data = request.get_json()
            required_fields = [
                "driver_license_number", "driver_license_expiry_date",
                "vehicle_brand", "vehicle_model", "vehicle_year",
                "license_plate_number", "vehicle_color", "number_of_seats",
                "bank_account_holder_name", "bank_account_number", "bank_name",
                "payment_method_preference"
            ]

            # Validate required fields
            for field in required_fields:
                exception_raiser(field not in data, "error", f"Missing field: {field}", 400)

            # Create driver entry
            new_driver = Driver(user_id=user_id, **data)
            db.session.add(new_driver)

            # Update user role
            user.role = UserRole.DRIVER
            db.session.commit()

            token = create_access_token(identity=user.get_identity(), additional_claims=user.get_additional_claims(),
                                        expires_delta=timedelta(days=1))
            response = jsonify({"status": "success", "message": "User is now a driver", "driver_profile": new_driver.to_dict(), "content": token})
            set_access_cookies(response, token)

            return response, 201

        except CustomHttpException as e:
            db.session.rollback()
            return jsonify({'status': e.status, "message": str(e)}), e.status_code
        except Exception as e:
            db.session.rollback()
            return jsonify({"status": "error", "message": str(e)}), 400

    # Show Become Driver form
    try:
        return render_template('becomeDriver.html')
    except TemplateNotFound:
        abort(404)