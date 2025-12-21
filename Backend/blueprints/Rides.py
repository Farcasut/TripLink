from flask import Blueprint, request, jsonify, current_app, abort
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from database import db
from blueprints.UserRoles import UserRoles
from models.RideOffer import RideOffer
from jinja2 import TemplateNotFound
from CustomHttpException import CustomHttpException
from CustomHttpException import exception_raiser
from CustomJWTRequired import jwt_noapi_required
from flask import Blueprint, render_template, abort, request, jsonify
from models.User import User
import FetchCities
from datetime import date, datetime, time
from sqlalchemy import and_

rides = Blueprint("rides", __name__, url_prefix="/rides")

@rides.post("/create")
@jwt_noapi_required
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
      - 201, if the ride was created
      - 403, if the user is not a driver
      - 400, db errors
  """
  try:
    jwt_map = get_jwt()
    user_id = int(get_jwt_identity())
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
def get_ride(ride_id: int):
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
    
@rides.post("/book/<int:ride_id>")
@jwt_required()
def book_ride(ride_id):
    """
    Allows a passenger to book a seat on a ride.
    Requires JWT token for authentication.

    Path param:
        ride_id (int): ID of the ride to book

    Returns:
        201 - Seat booked successfully
        400 - No seats left / Already booked
        404 - Ride not found
    """
    try:
        jwt_map = get_jwt()
        user_id = jwt_map.get("id")

        ride = RideOffer.query.get(ride_id)
        exception_raiser(ride is None, "error", "Ride not found.", 404)
        exception_raiser(ride.available_seats <= 0, "error", "No seats available", 400)


        user = User.query.get(user_id)
        exception_raiser(not user, "error", "User not found", 404)
        exception_raiser(user in ride.passengers, "error", "You already booked this ride", 400)


        ride.passengers.append(user)
        ride.available_seats -= 1
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Seat successfully booked",
            "content": ride.to_dict()
        }), 201

    except CustomHttpException as e:
        return jsonify({'status': e.status, "message": str(e)}), e.status_code
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

@rides.delete("/book/<int:ride_id>")
@jwt_required()
def cancel_booking(ride_id):
    try:
        jwt_map = get_jwt()
        user_id = jwt_map.get("id")

        ride = RideOffer.query.get(ride_id)
        exception_raiser(not ride, "error", "Ride not found", 404)
        user = User.query.get(user_id)
        exception_raiser(user not in ride.passengers, "error", "You have not booked this ride", 400)

        ride.passengers.remove(user)
        ride.available_seats += 1
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Booking canceled"
        }), 200

    except CustomHttpException as e:
        return jsonify({'status': e.status, "message": str(e)}), e.status_code
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

@rides.get("/")
@jwt_noapi_required
def search_rides():
    try:
        cities = FetchCities.get_all('romania')
        today = date.today().isoformat()
        return render_template('rides/search.html', cities = cities, today = today)
    except TemplateNotFound:
        abort(404)
    except Exception as e:
        if current_app.debug:
            print(f'search_rides: {e}.')
            breakpoint()

        raise

def estimate_trip_cost(distance_km, cost_per_km=0.12, service_fee=2.0):
    return round(distance_km * cost_per_km + service_fee, 2)

@rides.post("/search")
@jwt_noapi_required
def search_rides_results():
    try:
        from_city = request.form.get("from_city")
        to_city = request.form.get("to_city")
        date = request.form.get("date")
        dt = datetime.strptime(date, '%Y-%m-%d')

        sod = int(datetime.combine(dt, time.min).timestamp())
        eod = int(datetime.combine(dt, time.max).timestamp())

        rides = RideOffer.query.filter_by(
            source=from_city,
            destination=to_city,
        ).filter(and_(sod <= RideOffer.departure_date, RideOffer.departure_date <= eod)).all()

        ride_dates = [datetime.fromtimestamp(ride.departure_date).strftime('%Y-%m-%d %H:%M') for ride in rides]
        distance_km = FetchCities.distance(
            FetchCities.get_location(from_city, 'Romania'),
            FetchCities.get_location(to_city, 'Romania')
        )

        estimated_price = estimate_trip_cost(distance_km)
        return render_template(
            "rides/results.html",
            rides = list(zip(rides, ride_dates)),
            estimated_price = estimated_price,
            from_city = from_city,
            to_city = to_city,
            date = date,
        )
        
    except TemplateNotFound:
        abort(404)
    except Exception as e:
        if current_app.debug:
            print(f'search_rides_results: {e}.')
            breakpoint()
            
        raise
