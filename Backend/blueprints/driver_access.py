from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from models.Driver import Driver
from models.User import User
from blueprints.UserRoles import UserRoles
from CustomHttpException import exception_raiser, CustomHttpException

driver_access = Blueprint("driver_access", __name__, url_prefix="/driver")

@driver_access.post("/become_driver")
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
        user.role = UserRoles.DRIVER.value
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "User is now a driver",
            "driver_profile": new_driver.to_dict()
        }), 201

    except CustomHttpException as e:
        db.session.rollback()
        return jsonify({'status': e.status, "message": str(e)}), e.status_code
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400