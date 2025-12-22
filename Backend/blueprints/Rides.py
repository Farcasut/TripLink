from flask import Blueprint, redirect, request, jsonify, current_app, abort
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from database import db
from models.enums import UserRole,BookingStatus
from models.RideOffer import RideOffer
from jinja2 import TemplateNotFound
from CustomHttpException import CustomHttpException
from CustomHttpException import exception_raiser
from CustomJWTRequired import jwt_noapi_required
from flask import Blueprint, render_template, abort, request, jsonify
from models.User import User
from models.Booking import Booking
import FetchCities
from datetime import date, datetime, time
from sqlalchemy import and_


rides = Blueprint("rides", __name__, url_prefix="/rides")

def get_jwt_user(require_driver: bool = False):
    jwt_map = get_jwt()
    identity = get_jwt_identity()
    exception_raiser(identity is None, "error", "Not authenticated", 401)

    user_id = int(identity)
    role = jwt_map.get("role")

    if require_driver:
        exception_raiser(role != UserRole.DRIVER, "error", "Driver only", 403)

    return user_id, jwt_map

def base_context_from_jwt(jwt_map):
    return {
        "first_name": jwt_map.get("first_name", ""),
        "last_name": jwt_map.get("last_name", ""),
        "is_driver": jwt_map.get("role") == UserRole.DRIVER,
    }


def format_ts(ts: int) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")

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
    user_id, jwt_map = get_jwt_user(require_driver=True)
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
  
@rides.get("/create")
@jwt_noapi_required
def create_ride_form():
    """
    Render the create ride form (driver only).
    """
    try:
        jwt_map = get_jwt()
        user_role = jwt_map.get("role")
        
        # Redirect non-drivers
        exception_raiser(user_role != UserRole.DRIVER, "error", "You must be a driver to access this page.", 403)
        
        cities = FetchCities.get_all('romania')
        today = date.today().isoformat()
    
        return render_template(
            "rides/create.html",
            cities=cities,
            today=today,
            **base_context_from_jwt(jwt_map)
        )
        
    except CustomHttpException as e:
        return redirect('/dashboard')
    except TemplateNotFound:
        abort(404)
    except Exception as e:
        if current_app.debug:
            print(f'create_ride_form: {e}.')
            breakpoint()
        raise

@rides.get("/all_rides")
@jwt_noapi_required
def show_all_created_rides():
    user_id, jwt_map = get_jwt_user(require_driver=True)

    rides_found = (
        RideOffer.query
        .filter(RideOffer.author_id == user_id)
        .order_by(RideOffer.departure_date.asc())
        .all()
    )

    rides_data = [
        {
            "id": r.id,
            "source": r.source,
            "destination": r.destination,
            "available_seats": r.available_seats,
            "price": r.price,
            "departure_date": format_ts(r.departure_date),
        }
        for r in rides_found
    ]

    return render_template(
        "rides/all_rides.html",
        rides=rides_data,
        **base_context_from_jwt(jwt_map)
    )


@rides.get("/<int:ride_id>")
@jwt_required(optional=True)
def get_ride(ride_id):
    try:
        ride = RideOffer.query.get(ride_id)
        exception_raiser(not ride, "error", "Ride not found", 404)
        return jsonify({"status": "success", "content": ride.to_dict()}), 200
    except CustomHttpException as e:
        return jsonify({"status": e.status, "message": str(e)}), e.status_code
    
@rides.post("/cancel/<int:ride_id>")
@jwt_noapi_required
def cancel_ride(ride_id):
    user_id, _ = get_jwt_user(require_driver=True)

    ride = db.session.get(RideOffer, ride_id)
    exception_raiser(not ride, "error", "Ride not found", 404)
    exception_raiser(ride.author_id != user_id, "error", "Not your ride", 403)

    db.session.delete(ride)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Ride cancelled"
    }), 200


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
        user_id, jwt_map = get_jwt_user()

        from_city = request.form.get("from_city")
        to_city = request.form.get("to_city")
        search_date = request.form.get("date")

        if not from_city or not to_city or not search_date:
            return redirect("/rides", code=303)

        dt = datetime.strptime(search_date, "%Y-%m-%d")
        sod = int(datetime.combine(dt, time.min).timestamp())
        eod = int(datetime.combine(dt, time.max).timestamp())

        rides_found = (
            RideOffer.query
            .filter_by(source=from_city, destination=to_city)
            .filter(and_(sod <= RideOffer.departure_date,
                         RideOffer.departure_date <= eod))
            .all()
        )

        ride_ids = [r.id for r in rides_found]
        booked_ids = set()

        if ride_ids:
            booked_ids = {
                b.ride_id
                for b in Booking.query.filter(
                    Booking.passenger_id == user_id,
                    Booking.ride_id.in_(ride_ids),
                    Booking.status.in_([BookingStatus.PENDING, BookingStatus.ACCEPTED])
                ).all()
            }

        results = [
            (
                r,
                datetime.fromtimestamp(r.departure_date).strftime("%Y-%m-%d %H:%M"),
                r.id in booked_ids
            )
            for r in rides_found
        ]

        distance_km = FetchCities.distance(
            FetchCities.get_location(from_city, 'Romania'),
            FetchCities.get_location(to_city, 'Romania')
        )

        estimated_price = estimate_trip_cost(distance_km)
        
        return render_template(
            "rides/results.html",
            rides=results,
            estimated_price=estimated_price,
            from_city=from_city,
            to_city=to_city,
            date=search_date,
            **base_context_from_jwt(jwt_map)
        )

    except TemplateNotFound:
        abort(404)

