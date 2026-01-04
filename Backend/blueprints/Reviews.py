from flask import Blueprint, jsonify, render_template, abort, request
from flask_jwt_extended import get_jwt_identity
from database import db
from models.Review import Review
from models.Booking import Booking
from models.RideOffer import RideOffer
from models.User import User
from models.enums import BookingStatus
from CustomJWTRequired import jwt_noapi_required
from CustomHttpException import exception_raiser
from CustomHttpException import CustomHttpException
from jinja2 import TemplateNotFound
from blueprints.Rides import get_jwt_user, base_context_from_jwt
from sqlalchemy import and_, or_

reviews = Blueprint("reviews", __name__, url_prefix="/reviews")


@reviews.post("/create")
@jwt_noapi_required
def create_review():
  """
  Create a review for a completed booking.
  The reviewer must be either the driver or passenger of the booking.
  The reviewed person is the other party.
  """
  try:
    user_id, _jwt_map = get_jwt_user()

    data = request.get_json()
    if not data:
      return jsonify({"error": "No JSON data provided"}), 400

    booking_id = data.get("booking_id")
    rating = data.get("rating")
    comment = data.get("comment", "")

    exception_raiser(not booking_id, "error", "booking_id is required", 400)
    exception_raiser(not rating, "error", "rating is required", 400)
    exception_raiser(rating < 1 or rating > 5, "error", "rating must be between 1 and 5", 400)

    booking = db.session.get(Booking, booking_id)
    exception_raiser(not booking, "error", "Booking not found", 404)

    # Check if user is part of this booking
    is_driver = booking.ride.author_id == user_id
    is_passenger = booking.passenger_id == user_id

    exception_raiser(not (is_driver or is_passenger), "error", "You are not part of this booking", 403)

    # Only allow reviews for accepted bookings
    exception_raiser(booking.status != BookingStatus.ACCEPTED, "error", "Can only review accepted bookings", 400)

    # Determine who is being reviewed
    if is_driver:
      reviewed_id = booking.passenger_id
    else:
      reviewed_id = booking.ride.author_id

    # Check if review already exists
    existing_review = Review.query.filter_by(booking_id=booking_id, reviewer_id=user_id).first()

    exception_raiser(existing_review, "error", "You have already reviewed this booking", 400)

    # Create the review
    review = Review(booking_id=booking_id, reviewer_id=user_id, reviewed_id=reviewed_id, rating=rating, comment=comment)

    db.session.add(review)
    db.session.commit()

    return jsonify({"message": "Review created successfully", "review": review.to_dict()}), 201

  except CustomHttpException as e:
    return jsonify({'status': e.status, "message": str(e)}), e.status_code
  except Exception as e:
    return jsonify({"error": str(e)}), 500


@reviews.get("/user/<int:user_id>")
@jwt_noapi_required
def get_user_reviews(user_id):
  """
  Get all reviews for a specific user (both as driver and passenger).
  Can return JSON or render template based on Accept header.
  """
  try:
    _current_user_id, jwt_map = get_jwt_user()

    user = db.session.get(User, user_id)
    exception_raiser(not user, "error", "User not found", 404)

    # Get all reviews where this user was reviewed
    reviews_list = Review.query.filter_by(reviewed_id=user_id).all()

    # Calculate average rating
    if reviews_list:
      avg_rating = sum(r.rating for r in reviews_list) / len(reviews_list)
      total_reviews = len(reviews_list)
    else:
      avg_rating = 0
      total_reviews = 0

    # Check if request wants JSON (API call) or HTML (browser)
    wants_json = request.args.get('format') == 'json' or request.headers.get('Accept', '').find(
      'application/json') != -1

    if wants_json:
      return jsonify({"user_id": user_id, "average_rating": round(avg_rating, 2), "total_reviews": total_reviews,
        "reviews": [r.to_dict() for r in reviews_list]}), 200
    else:
      return render_template("reviews/user_reviews.html", reviewed_user=user, reviews=reviews_list,
        avg_rating=round(avg_rating, 2), total_reviews=total_reviews, **base_context_from_jwt(jwt_map))

  except CustomHttpException as e:
    return jsonify({'status': e.status, "message": str(e)}), e.status_code
  except TemplateNotFound:
    abort(404)


@reviews.get("/booking/<int:booking_id>")
@jwt_noapi_required
def get_booking_reviews(booking_id):
  """
  Get all reviews for a specific booking.
  """
  try:
    user_id, _jwt_map = get_jwt_user()

    booking = db.session.get(Booking, booking_id)
    exception_raiser(not booking, "error", "Booking not found", 404)

    # Check if user is part of this booking
    is_driver = booking.ride.author_id == user_id
    is_passenger = booking.passenger_id == user_id

    exception_raiser(not (is_driver or is_passenger), "error", "You are not part of this booking", 403)

    reviews_list = Review.query.filter_by(booking_id=booking_id).all()

    return jsonify({"booking_id": booking_id, "reviews": [r.to_dict() for r in reviews_list]}), 200

  except CustomHttpException as e:
    return jsonify({'status': e.status, "message": str(e)}), e.status_code


@reviews.delete("/<int:review_id>")
@jwt_noapi_required
def delete_review(review_id):
  """
  Delete a review (only the reviewer can delete their own review).
  """
  try:
    user_id, _jwt_map = get_jwt_user()

    review = db.session.get(Review, review_id)
    exception_raiser(not review, "error", "Review not found", 404)
    exception_raiser(review.reviewer_id != user_id, "error", "You can only delete your own reviews", 403)

    db.session.delete(review)
    db.session.commit()

    return jsonify({"message": "Review deleted successfully"}), 200

  except CustomHttpException as e:
    return jsonify({'status': e.status, "message": str(e)}), e.status_code


@reviews.get("/my")
@jwt_noapi_required
def my_reviews():
  """
  Get all reviews written by the current user.
  """
  try:
    user_id, jwt_map = get_jwt_user()

    reviews_list = Review.query.filter_by(reviewer_id=user_id).all()

    # Format reviews with additional info for template
    formatted_reviews = []
    for review in reviews_list:
      formatted_review = {"id": review.id, "rating": review.rating, "comment": review.comment,
        "created_at": review.created_at.strftime("%Y-%m-%d %H:%M") if review.created_at else "",
        "booking_info": {"id": review.booking.id, "source": review.booking.ride.source,
          "destination": review.booking.ride.destination, },
        "reviewed_user": {"id": review.reviewed.id, "username": review.reviewed.username,
          "first_name": review.reviewed.first_name, "last_name": review.reviewed.last_name, }}
      formatted_reviews.append(formatted_review)

    return render_template("reviews/my_reviews.html", reviews=formatted_reviews, **base_context_from_jwt(jwt_map))
  except TemplateNotFound:
    abort(404)
