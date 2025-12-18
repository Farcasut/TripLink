from flask import Blueprint, jsonify, redirect, render_template, abort
from flask_jwt_extended import get_current_user, get_jwt_identity
from datetime import datetime

from database import db
from models.Booking import Booking
from models.RideOffer import RideOffer
from models.enums import UserRole, BookingStatus

from CustomJWTRequired import jwt_noapi_required
from CustomHttpException import exception_raiser
from jinja2 import TemplateNotFound

bookings = Blueprint("bookings", __name__, url_prefix="/bookings")

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

@bookings.get("/incoming")
@jwt_noapi_required
def incoming_bookings():
    try:
        user = require_driver()

        bookings_list = (
            Booking.query
            .join(RideOffer)
            .filter(
                RideOffer.author_id == user.id,
                Booking.status == BookingStatus.PENDING
            )
            .all()
        )

        for b in bookings_list:
            b.departure_display = format_ts(b.ride.departure_date)

        return render_template(
            "bookings/incoming_bookings.html",
            bookings=bookings_list,
            **base_context(user)
        )
    except TemplateNotFound:
        abort(404)


@bookings.get("/my")
@jwt_noapi_required
def my_bookings():
    try:
        user = get_current_user()

        bookings_list = Booking.query.filter_by(
            passenger_id=user.id
        ).all()

        for b in bookings_list:
            b.departure_display = format_ts(b.ride.departure_date)

        return render_template(
            "bookings/my_bookings.html",
            bookings=bookings_list,
            **base_context(user)
        )
    except TemplateNotFound:
        abort(404)

@bookings.post("/request/<int:ride_id>")
@jwt_noapi_required
def request_booking(ride_id):
    user_id = int(get_jwt_identity())
    ride = db.session.get(RideOffer, ride_id)
    exception_raiser(not ride, "error", "Ride not found", 404)

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


@bookings.post("/accept/<int:booking_id>")
@jwt_noapi_required
def accept_booking(booking_id):
    user = require_driver()
    booking = db.session.get(Booking, booking_id)
    exception_raiser(not booking, "error", "Booking not found", 404)

    ride = booking.ride
    exception_raiser(ride.author_id != user.id, "error", "Not your ride", 403)
    exception_raiser(ride.available_seats <= 0, "error", "No seats left", 400)

    booking.status = BookingStatus.ACCEPTED
    ride.available_seats -= 1
    db.session.commit()

    return jsonify({"message": "Booking accepted"}), 200


@bookings.post("/deny/<int:booking_id>")
@jwt_noapi_required
def deny_booking(booking_id):
    user = require_driver()
    booking = db.session.get(Booking, booking_id)
    exception_raiser(not booking, "error", "Booking not found", 404)

    exception_raiser(
        booking.ride.author_id != user.id,
        "error",
        "Not your ride",
        403
    )

    booking.status = BookingStatus.DENIED
    db.session.commit()

    return jsonify({"message": "Booking denied"}), 200


@bookings.post("/delete/<int:booking_id>")
@jwt_noapi_required
def delete_booking(booking_id):
    user = get_current_user()
    booking = db.session.get(Booking, booking_id)
    exception_raiser(not booking, "error", "Booking not found", 404)
    exception_raiser(booking.passenger_id != user.id, "error", "Not your booking", 403)

    if booking.status == BookingStatus.ACCEPTED:
        booking.ride.available_seats += 1

    db.session.delete(booking)
    db.session.commit()

    return redirect("/bookings/my")
