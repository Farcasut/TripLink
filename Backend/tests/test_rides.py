import json
import pytest
from flask_jwt_extended import create_access_token
from database import db
from models.RideOffer import RideOffer
from models.enums import UserRole


@pytest.fixture
def driver_token(mock_app):
  with mock_app.app_context():
    token = create_access_token(identity="1", additional_claims={"id": "1", "role": UserRole.DRIVER})
    return token


@pytest.fixture
def passenger_token(mock_app):
  with mock_app.app_context():
    token = create_access_token(identity="2", additional_claims={"id": "2", "role": UserRole.DEFAULT})
    return token


def test_create_ride_success(client, driver_token):
  payload = {"source": "Bucuresti", "destination": "Cluj", "departure_date": 1700000000, "price": 50,
             "available_seats": 3}
  response = client.post("/rides/create", content_type="application/json", json=payload,
                         headers={"Authorization": f"Bearer {driver_token}"})
  data = response.get_json()
  assert response.status_code == 201
  assert data["status"] == "success"
  assert data["content"]["source"] == "Bucuresti"
  assert data["content"]["destination"] == "Cluj"


def test_create_ride_forbidden_for_passenger(client, passenger_token):
  payload = {"source": "City A", "destination": "City B", "departure_date": 1700000000, "price": 50,
             "available_seats": 3}
  response = client.post("/rides/create", data=json.dumps(payload), content_type="application/json",
                         headers={"Authorization": f"Bearer {passenger_token}"})
  data = response.get_json()
  assert response.status_code == 403
  assert data["status"] == "error"


def test_get_ride(client, driver_token):
  with client.application.app_context():
    ride = RideOffer(author_id=1, source="City A", destination="City B", departure_date=1700000000, price=50,
                     available_seats=3)
    db.session.add(ride)
    db.session.commit()
    ride_id = ride.id

  response = client.get(f"/rides/{ride_id}", headers={"Authorization": f"Bearer {driver_token}"})
  data = response.get_json()
  assert response.status_code == 200
  assert data["status"] == "success"
  assert data["content"]["id"] == ride_id


def test_get_ride_not_found(client, driver_token):
  response = client.get("/rides/9999", headers={"Authorization": f"Bearer {driver_token}"})
  data = response.get_json()
  assert response.status_code == 404
  assert data["status"] == "error"

def test_book_ride_success(client, driver_token, passenger_token):
    # First, create a ride (as driver)
    payload = {
        "source": "Bucuresti",
        "destination": "Brasov",
        "departure_date": 1700000000,
        "price": 100,
        "available_seats": 2
    }
    create_response = client.post(
        "/rides/create",
        content_type="application/json",
        json=payload,
        headers={"Authorization": f"Bearer {driver_token}"}
    )
    ride_id = create_response.get_json()["content"]["id"]

    # Book ride as passenger
    book_response = client.post(
        f"/bookings/request/{ride_id}",
        headers={"Authorization": f"Bearer {passenger_token}"}
    )
    data = book_response.get_json()

    assert book_response.status_code == 201
    assert "Booking request sent" in data["message"]

    # Verify seat count decreased
    # with client.application.app_context():
    #     updated_ride = RideOffer.query.get(ride_id)
    #     assert updated_ride.available_seats == 1
    #     assert len(updated_ride.passengers) == 1
    # TODO(fix): The driver has to accept your booking for the seats to decrease.


def test_book_ride_no_seats_left(client, driver_token, passenger_token):
    # Create ride with 0 seats
    payload = {
        "source": "Bucuresti",
        "destination": "Sibiu",
        "departure_date": 1700000000,
        "price": 80,
        "available_seats": 0
    }
    create_response = client.post(
        "/rides/create",
        content_type="application/json",
        json=payload,
        headers={"Authorization": f"Bearer {driver_token}"}
    )
    ride_id = create_response.get_json()["content"]["id"]

    # Try to book as passenger
    book_response = client.post(
        f"/bookings/request/{ride_id}",
        headers={"Authorization": f"Bearer {passenger_token}"}
    )
    data = book_response.get_json()

    assert book_response.status_code == 400
    assert data["status"] == "error"
    assert "No seats available" in data["message"]


def test_book_ride_already_booked(client, driver_token, passenger_token):
    # Create a ride
    payload = {
        "source": "Iasi",
        "destination": "Cluj",
        "departure_date": 1700000000,
        "price": 75,
        "available_seats": 2
    }
    create_response = client.post(
        "/rides/create",
        content_type="application/json",
        json=payload,
        headers={"Authorization": f"Bearer {driver_token}"}
    )
    ride_id = create_response.get_json()["content"]["id"]

    # Book once
    client.post(f"/bookings/request/{ride_id}", headers={"Authorization": f"Bearer {passenger_token}"})
    # Try booking again
    second_book = client.post(f"/bookings/request/{ride_id}", headers={"Authorization": f"Bearer {passenger_token}"})
    data = second_book.get_json()

    assert second_book.status_code == 400
    assert data["status"] == "error"
    assert "already booked" in data["message"].lower()


def test_book_ride_not_found(client, passenger_token):
    response = client.post("/bookings/request/9999", headers={"Authorization": f"Bearer {passenger_token}"})
    data = response.get_json()
    assert response.status_code == 404
    assert data["status"] == "error"
    assert "not found" in data["message"].lower()