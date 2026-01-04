from flask import Blueprint, jsonify, render_template, abort, request
from flask_jwt_extended import get_jwt_identity
from database import db
from models.Booking import Booking
from models.RideOffer import RideOffer
from models.Review import Review
from models.User import User
from models.enums import BookingStatus
from CustomJWTRequired import jwt_noapi_required
from CustomHttpException import exception_raiser
from CustomHttpException import CustomHttpException
from jinja2 import TemplateNotFound
from sqlalchemy import or_

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
            # Calculate passenger's average rating
            passenger_reviews = Review.query.filter_by(reviewed_id=b.passenger_id).all()
            if passenger_reviews:
                b.passenger_avg_rating = round(sum(rev.rating for rev in passenger_reviews) / len(passenger_reviews), 2)
                b.passenger_total_reviews = len(passenger_reviews)
            else:
                b.passenger_avg_rating = 0
                b.passenger_total_reviews = 0

        return render_template(
            "bookings/incoming_bookings.html",
            bookings=bookings_list,
            **base_context_from_jwt(jwt_map)
        )
    except TemplateNotFound:
        abort(404)


@bookings.get("/accepted_driver")
@jwt_noapi_required
def accepted_driver_bookings():
    """
    Get all accepted bookings for the current driver.
    This shows passengers that can be reviewed.
    Supports search functionality.
    """
    try:
        user_id, jwt_map = get_jwt_user(require_driver=True)

        search_query = request.args.get("search", "").strip()

        query = (
            Booking.query
            .join(RideOffer)
            .join(User, Booking.passenger_id == User.id)
            .filter(
                RideOffer.author_id == user_id,
                Booking.status == BookingStatus.ACCEPTED
            )
        )

        if search_query:
            search_term = f"%{search_query}%"
            query = query.filter(
                or_(
                    User.username.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term)
                )
            )

        bookings_list = query.all()

        for b in bookings_list:
            b.departure_display = format_ts(b.ride.departure_date)
            # Check if driver has already reviewed this booking
            existing_review = Review.query.filter_by(
                booking_id=b.id,
                reviewer_id=user_id
            ).first()
            b.has_reviewed = existing_review is not None
            b.review_id = existing_review.id if existing_review else None

        return render_template(
            "bookings/accepted_driver_bookings.html",
            bookings=bookings_list,
            search_query=search_query,
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
            # Check if user has already reviewed this booking
            existing_review = Review.query.filter_by(
                booking_id=b.id,
                reviewer_id=user_id
            ).first()
            b.has_reviewed = existing_review is not None
            b.review_id = existing_review.id if existing_review else None

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


@bookings.get("/accepted")
@jwt_noapi_required
def accepted_bookings():
    """
    Get all accepted bookings for the current user (as driver or passenger).
    This is used to show bookings that can be reviewed.
    """
    try:
        user_id, jwt_map = get_jwt_user()

        # Get bookings where user is passenger
        passenger_bookings = Booking.query.filter_by(
            passenger_id=user_id,
            status=BookingStatus.ACCEPTED
        ).all()

        # Get bookings where user is driver
        driver_bookings = (
            Booking.query
            .join(RideOffer)
            .filter(
                RideOffer.author_id == user_id,
                Booking.status == BookingStatus.ACCEPTED
            )
            .all()
        )

        all_bookings = passenger_bookings + driver_bookings

        for b in all_bookings:
            b.departure_display = format_ts(b.ride.departure_date)
            # Check if user has already reviewed this booking
            existing_review = Review.query.filter_by(
                booking_id=b.id,
                reviewer_id=user_id
            ).first()
            b.has_reviewed = existing_review is not None
            b.review_id = existing_review.id if existing_review else None
            # Determine who should be reviewed
            if b.passenger_id == user_id:
                b.review_target_id = b.ride.author_id
                b.review_target_name = f"{b.ride.author.first_name} {b.ride.author.last_name}"
            else:
                b.review_target_id = b.passenger_id
                b.review_target_name = f"{b.passenger.first_name} {b.passenger.last_name}"

        return render_template(
            "bookings/accepted_bookings.html",
            bookings=all_bookings,
            **base_context_from_jwt(jwt_map)
        )
    except TemplateNotFound:
        abort(404)

