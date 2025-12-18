from flask import (
    Blueprint, request, jsonify,
    render_template, redirect, abort
)
from flask_jwt_extended import get_current_user, jwt_required
from datetime import date, datetime, time
from sqlalchemy import and_

from database import db
from models.RideOffer import RideOffer
from models.enums import UserRole
from CustomJWTRequired import jwt_noapi_required
from CustomHttpException import CustomHttpException, exception_raiser
from jinja2 import TemplateNotFound
import FetchCities

rides = Blueprint("rides", __name__, url_prefix="/rides")


def require_driver():
    user = get_current_user()
    exception_raiser(user is None, "error", "Not authenticated", 401)
    exception_raiser(user.role != UserRole.DRIVER, "error", "Driver only", 403)
    return user


def base_context(user):
    return {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_driver": user.role == UserRole.DRIVER
    }


def format_ts(ts: int) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


@rides.get("/")
@jwt_noapi_required
def search_rides():
    try:
        user = get_current_user()
        cities = FetchCities.get_all("romania")
        today = date.today().isoformat()

        return render_template(
            "rides/search.html",
            cities=cities,
            today=today,
            **base_context(user)
        )
    except TemplateNotFound:
        abort(404)


@rides.post("/search")
@jwt_noapi_required
def search_rides_results():
    try:
        user = get_current_user()

        from_city = request.form.get("from_city")
        to_city = request.form.get("to_city")
        search_date = request.form.get("date")

        dt = datetime.strptime(search_date, "%Y-%m-%d")
        sod = int(datetime.combine(dt, time.min).timestamp())
        eod = int(datetime.combine(dt, time.max).timestamp())

        rides_found = RideOffer.query.filter_by(
            source=from_city,
            destination=to_city,
        ).filter(
            and_(sod <= RideOffer.departure_date,
                 RideOffer.departure_date <= eod)
        ).all()

        results = [
            (r, format_ts(r.departure_date),
             any(b.passenger_id == user.id for b in r.bookings))
            for r in rides_found
        ]

        return render_template(
            "rides/results.html",
            rides=results,
            from_city=from_city,
            to_city=to_city,
            date=search_date,
            **base_context(user)
        )
    except TemplateNotFound:
        abort(404)

@rides.post("/create")
@jwt_noapi_required
def create_ride():
    user = require_driver()

    data = request.get_json()
    exception_raiser(not data, "error", "Invalid JSON body", 400)

    source = data.get("source")
    destination = data.get("destination")
    departure_date = data.get("departure_date")
    price = data.get("price")
    available_seats = data.get("available_seats")

    exception_raiser(not source or not destination, "error", "Source and destination required", 400)
    exception_raiser(not isinstance(departure_date, int), "error", "Invalid departure date", 400)
    exception_raiser(available_seats is None or available_seats <= 0, "error", "Invalid seats", 400)
    exception_raiser(price is None or price < 0, "error", "Invalid price", 400)

    ride = RideOffer(
        source=source,
        destination=destination,
        departure_date=departure_date,
        price=price,
        available_seats=available_seats,
        author_id=user.id
    )

    db.session.add(ride)
    db.session.commit()

    return jsonify({"message": "Ride created"}), 201


@rides.get("/create")
@jwt_noapi_required
def create_ride_page():
    try:
        user = require_driver()
        return render_template(
            "rides/create.html",
            **base_context(user)
        )
    except TemplateNotFound:
        abort(404)


@rides.get("/all_rides")
@jwt_noapi_required
def show_all_created_rides():
    user = require_driver()

    rides_found = RideOffer.query.filter(
        RideOffer.author_id == user.id
    ).order_by(RideOffer.departure_date.asc()).all()

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
        **base_context(user)
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
    user = require_driver()

    ride = db.session.get(RideOffer, ride_id)
    exception_raiser(not ride, "error", "Ride not found", 404)
    exception_raiser(ride.author_id != user.id, "error", "Not your ride", 403)

    db.session.delete(ride)
    db.session.commit()

    return redirect("/rides/all_rides")

