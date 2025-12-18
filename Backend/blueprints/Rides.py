from flask import Blueprint, redirect, request, jsonify, current_app, abort
from flask_jwt_extended import get_current_user, jwt_required, get_jwt_identity, get_jwt
from models.Booking import Booking
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


#Modific din db in jwt dupa
@rides.get("/create")
@jwt_noapi_required
def create_ride_page():
    try:
        user = get_current_user()
        exception_raiser(user is None, "error", "Not authenticated", 401)
        exception_raiser(user.role != UserRoles.DRIVER.value, "error", "Driver only", 403)

        return render_template(
            "rides/create.html",
            role=user.role,
            first_name=user.first_name,
            last_name=user.last_name
        )
    except TemplateNotFound:
        abort(404)
    except Exception as e:
        if current_app.debug:
            print(f'create_ride_page: {e}.')
            breakpoint()
        raise


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
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        exception_raiser(user is None, "error", "User not found", 404)
        exception_raiser(user.role != UserRoles.DRIVER.value, "error", "You must be a driver...", 403)

        ride = RideOffer(**request.get_json())
        ride.author_id = user.id

        db.session.add(ride)
        db.session.commit()

        return jsonify({"status": "success", "message": "Ride added", "content": ride.to_dict()}), 201
    except CustomHttpException as e:
        return jsonify({'status': e.status, "message": str(e)}), e.status_code
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400


@rides.post("/cancel/<int:ride_id>")
@jwt_noapi_required
def cancel_ride(ride_id):
    user = get_current_user()
    exception_raiser(user is None, "error", "Not authenticated", 401)
    exception_raiser(user.role != UserRoles.DRIVER.value, "error", "Driver only", 403)

    ride = RideOffer.query.get(ride_id)
    exception_raiser(not ride, "error", "Ride not found", 404)
    exception_raiser(ride.author_id != user.id, "error", "Not your ride", 403)

    db.session.delete(ride)
    db.session.commit()

    return redirect("/rides/all_rides")

@rides.get("/all_rides")
@jwt_noapi_required
def show_all_created_rides():
    try:
        user = get_current_user()
        exception_raiser(user is None, "error", "Not authenticated", 401)
        exception_raiser(user.role != UserRoles.DRIVER.value, "error", "Driver only", 403)

        now_ts = int(datetime.now().timestamp())

        rides = RideOffer.query.filter(
            RideOffer.author_id == user.id,
            RideOffer.departure_date > now_ts
        ).order_by(RideOffer.departure_date.asc()).all()

        formatted_rides = []
        for ride in rides:
            formatted_rides.append({
                "id": ride.id,
                "source": ride.source,
                "destination": ride.destination,
                "available_seats": ride.available_seats,
                "price": ride.price,
                "departure_date": datetime.fromtimestamp(
                    ride.departure_date
                ).strftime("%Y-%m-%d %H:%M")
            })

        return render_template(
            "rides/all_rides.html",
            rides=formatted_rides,
            role=user.role,
            first_name=user.first_name,
            last_name=user.last_name
        )

    except TemplateNotFound:
        abort(404)
    except Exception as e:
        if current_app.debug:
            print(f'all_rides: {e}')
            breakpoint()
        raise

    
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
def request_booking(ride_id):
    user_id = int(get_jwt_identity())

    ride = db.session.get(RideOffer, ride_id)
    exception_raiser(not ride, "error", "Ride not found", 404)

    booking = Booking(
        ride_id=ride.id,
        passenger_id=user_id,
        status="pending"
    )

    db.session.add(booking)
    db.session.commit()

    return jsonify({"message": "Booking request sent"}), 201

@rides.post("/booking/<int:booking_id>/delete")
@jwt_noapi_required
def delete_booking(booking_id):
    user = get_current_user()

    booking = db.session.get(Booking, booking_id)
    exception_raiser(not booking, "error", "Booking not found", 404)

    exception_raiser(
        booking.passenger_id != user.id,
        "error",
        "Not your booking",
        403
    )

    ride = booking.ride

    if booking.status == "accepted":
        ride.available_seats += 1

    db.session.delete(booking)
    db.session.commit()

    return redirect("/rides/my_bookings")

@rides.get("/my_bookings")
@jwt_noapi_required
def my_bookings():
    user = get_current_user()

    bookings = Booking.query.filter_by(
        passenger_id=user.id
    ).all()

    for booking in bookings:
        booking.departure_display = datetime.fromtimestamp(
            booking.ride.departure_date
        ).strftime("%Y-%m-%d %H:%M")

    return render_template(
        "rides/my_bookings.html",
        bookings=bookings
    )

@rides.get("/bookings/<int:ride_id>")
@jwt_noapi_required
def view_bookings(ride_id):
    user = get_current_user()
    ride = db.session.get(RideOffer, ride_id)

    exception_raiser(ride.author_id != user.id, "error", "Not your ride", 403)

    bookings = Booking.query.filter_by(
        ride_id=ride_id,
        status="pending"
    ).all()

    return render_template(
        "rides/bookings.html",
        bookings=bookings
    )

@rides.post("/booking/<int:booking_id>/accept")
@jwt_noapi_required
def accept_booking(booking_id):
    user = get_current_user()
    booking = db.session.get(Booking, booking_id)
    exception_raiser(not booking, "error", "Booking not found", 404)

    ride = booking.ride
    exception_raiser(ride.author_id != user.id, "error", "Not your ride", 403)
    exception_raiser(ride.available_seats <= 0, "error", "No seats left", 400)

    booking.status = "accepted"
    ride.available_seats -= 1
    db.session.commit()

    return jsonify({"message": "Booking accepted"}), 200

@rides.post("/booking/<int:booking_id>/deny")
@jwt_noapi_required
def deny_booking(booking_id):
    user = get_current_user()
    booking = db.session.get(Booking, booking_id)
    exception_raiser(not booking, "error", "Booking not found", 404)

    ride = booking.ride
    exception_raiser(ride.author_id != user.id, "error", "Not your ride", 403)

    booking.status = "denied"
    db.session.commit()

    return jsonify({"message": "Booking denied"}), 200

@rides.get("/incoming_bookings")
@jwt_noapi_required
def incoming_bookings():
    user = get_current_user()
    exception_raiser(user is None, "error", "Not authenticated", 401)
    exception_raiser(user.role != UserRoles.DRIVER.value, "error", "Driver only", 403)

    bookings = (
        Booking.query
        .join(RideOffer)
        .filter(
            RideOffer.author_id == user.id,
            Booking.status == "pending"
        )
        .all()
    )

    for booking in bookings:
        booking.departure_display = datetime.fromtimestamp(
            booking.ride.departure_date
        ).strftime("%Y-%m-%d %H:%M")

        booking.seats_left = booking.ride.available_seats
        booking.driver = booking.ride.author

    return render_template(
        "rides/incoming_bookings.html",
        bookings=bookings,
        role=user.role,
        first_name=user.first_name,
        last_name=user.last_name
    )


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

        user = get_current_user()

        results = []
        for ride in rides:
            already_booked = Booking.query.filter_by(
                ride_id=ride.id,
                passenger_id=user.id
            ).first() is not None

            results.append((
                ride,
                datetime.fromtimestamp(ride.departure_date).strftime('%Y-%m-%d %H:%M'),
                already_booked
            ))


        return render_template(
            "rides/results.html",
            rides=results,
            from_city=from_city,
            to_city=to_city,
            date=date,
        )
        
    except TemplateNotFound:
        abort(404)
    except Exception as e:
        if current_app.debug:
            print(f'search_rides_results: {e}.')
            breakpoint()
            
        raise

