from flask import Blueprint, jsonify, render_template, abort
from flask_jwt_extended import get_jwt_identity
from database import db
from models.Booking import Booking
from models.RideOffer import RideOffer
from models.enums import BookingStatus
from CustomJWTRequired import jwt_noapi_required
from CustomHttpException import exception_raiser
from CustomHttpException import CustomHttpException
from jinja2 import TemplateNotFound

from blueprints.Rides import get_jwt_user, base_context_from_jwt, format_ts

bookings = Blueprint("bookings", __name__, url_prefix="/bookings")


@bookings.get("/incoming")
@jwt_noapi_required
def incoming_bookings():
    try:
        user_id, jwt_map = get_jwt_user(require_driver=True)

        bookings_list = (
            Booking.query
            .join(RideOffer)
            .filter(
                RideOffer.author_id == user_id,
                Booking.status == BookingStatus.PENDING
            )
            .all()
        )

        for b in bookings_list:
            b.departure_display = format_ts(b.ride.departure_date)

        return render_template(
            "bookings/incoming_bookings.html",
            bookings=bookings_list,
            **base_context_from_jwt(jwt_map)
        )
    except TemplateNotFound:
        abort(404)



@bookings.get("/my")
@jwt_noapi_required
def my_bookings():
    try:
        user_id, jwt_map = get_jwt_user()

        bookings_list = Booking.query.filter_by(
            passenger_id=user_id
        ).all()

        for b in bookings_list:
            b.departure_display = format_ts(b.ride.departure_date)

        return render_template(
            "bookings/my_bookings.html",
            bookings=bookings_list,
            **base_context_from_jwt(jwt_map)
        )
    except TemplateNotFound:
        abort(404)

@bookings.post("/request/<int:ride_id>")
@jwt_noapi_required
def request_booking(ride_id):
    try:
        user_id, _jwt_map = get_jwt_user()

        ride: RideOffer = db.session.get(RideOffer, ride_id)
        exception_raiser(not ride, "error", "Ride not found", 404)
        exception_raiser(ride.available_seats <= 0, "error", "No seats available", 400)

        exception_raiser(
            Booking.query.filter_by(
                ride_id=ride.id,
                passenger_id=user_id
            ).first(),
            "error",
            "Already booked",
            400
        )

        booking = Booking(
            ride_id=ride.id,
            passenger_id=user_id,
            status=BookingStatus.PENDING
        )

        db.session.add(booking)
        db.session.commit()

        return jsonify({"message": "Booking request sent"}), 201
    except CustomHttpException as e:
        return jsonify({'status': e.status, "message": str(e)}), e.status_code


@bookings.post("/accept/<int:booking_id>")
@jwt_noapi_required
def accept_booking(booking_id):
    user_id, _jwt_map = get_jwt_user(require_driver=True)

    booking = db.session.get(Booking, booking_id)
    exception_raiser(not booking, "error", "Booking not found", 404)

    ride = booking.ride
    exception_raiser(ride.author_id != user_id, "error", "Not your ride", 403)
    exception_raiser(ride.available_seats <= 0, "error", "No seats left", 400)

    booking.status = BookingStatus.ACCEPTED
    ride.available_seats -= 1
    db.session.commit()

    return jsonify({"message": "Booking accepted"}), 200


@bookings.post("/deny/<int:booking_id>")
@jwt_noapi_required
def deny_booking(booking_id):
    user_id, _jwt_map = get_jwt_user(require_driver=True)

    booking = db.session.get(Booking, booking_id)
    exception_raiser(not booking, "error", "Booking not found", 404)
    exception_raiser(booking.ride.author_id != user_id, "error", "Not your ride", 403)

    booking.status = BookingStatus.DENIED
    db.session.commit()

    return jsonify({"message": "Booking denied"}), 200

@bookings.post("/delete/<int:booking_id>")
@jwt_noapi_required
def delete_booking(booking_id):
    user_id, _jwt_map = get_jwt_user()

    booking = db.session.get(Booking, booking_id)
    exception_raiser(not booking, "error", "Booking not found", 404)
    exception_raiser(booking.passenger_id != user_id, "error", "Not your booking", 403)

    if booking.status == BookingStatus.ACCEPTED:
        booking.ride.available_seats += 1

    db.session.delete(booking)
    db.session.commit()

    return jsonify({"message": "Booking deleted"}), 200

