from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from database import db
from blueprints.UserRoles import UserRoles
from models.RideOffer import RideOffer
import time
from CustomHttpException import CustomHttpException
from CustomHttpException import exception_raiser
from flask import Blueprint, render_template, abort, request, jsonify

rides = Blueprint("rides", __name__, url_prefix="/rides")


@rides.post("/create")
@jwt_required()
def create_ride():
  """
  Create a new ride offer (driver only).
  Requires JWT token for authentication.

  Expects JSON payload:
      {
        source: "string",
        destination: "string"
        departure_date: "int" #unix timestamp
        price: "int"
        available_seats: "int"
      }
  Returns:
      JSON representation of the ride.
      -  201, if the ride was
      - 403, if the user is not a driver
      - 400, db errors
  """
  try:
    jwt_map = get_jwt()
    user_id = jwt_map.get("id")
    user_role = jwt_map.get("role")
    exception_raiser(user_role != UserRoles.DRIVER.value, "error", "You must be a driver to create a ride.", 403)
    ride: RideOffer = RideOffer(**request.get_json())
    ride.author_id = user_id
    db.session.add(ride)
    db.session.commit()
    return jsonify({"status": "success", "message": "Ride added with success", "content": ride.to_dict()}), 201

  except CustomHttpException as e:
    return jsonify({'status': e.status, "message": str(e)}), e.status_code
  except Exception as e:
    db.session.rollback()
    return jsonify({"status": "error", "message": str(e)}), 400

@rides.get("/<int:ride_id>")
@jwt_required(optional=True)
def get_ride(ride_id):
    """
    Retrieve a single ride offer by its ID.
    """
    try:
        ride = RideOffer.query.get(ride_id)
        exception_raiser(ride is None, "error", "Ride not found.", 404)

        return jsonify({
            "status": "success",
            "content": ride.to_dict()
        }), 200

    except CustomHttpException as e:
        return jsonify({'status': e.status, "message": str(e)}), e.status_code
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


