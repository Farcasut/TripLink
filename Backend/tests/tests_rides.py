import json
import pytest
from flask_jwt_extended import create_access_token
from database import db
from models.RideOffer import RiderOffer
from blueprints.UserRoles import UserRoles


@pytest.fixture
def driver_token(mock_app):
  with mock_app.app_context():
    token = create_access_token(identity="1", additional_claims={"id": "1", "role": UserRoles.DRIVER.value})
    return token


@pytest.fixture
def passenger_token(mock_app):
  with mock_app.app_context():
    token = create_access_token(identity="2", additional_claims={"id": "2", "role": UserRoles.DEFAULT.value})
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
    ride = RiderOffer(author_id=1, source="City A", destination="City B", departure_date=1700000000, price=50,
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

