from models.Driver import Driver
from models.enums import UserRole
from database import db
from unittest.mock import patch
from jinja2 import TemplateNotFound

VALID_DRIVER_DATA = {
    "driver_license_number": "DL123456",
    "driver_license_expiry_date": "2030-01-01",
    "vehicle_brand": "Toyota",
    "vehicle_model": "Corolla",
    "vehicle_year": 2020,
    "license_plate_number": "ABC-123",
    "vehicle_color": "Blue",
    "number_of_seats": 4,
    "bank_account_holder_name": "John Doe",
    "bank_account_number": "123456789",
    "bank_name": "Test Bank",
    "payment_method_preference": "Bank Transfer"
}
def test_become_driver_success(client, user, auth_headers):
    response = client.post(
        "/driver/becomeDriver",
        json=VALID_DRIVER_DATA,
        headers=auth_headers
    )

    assert response.status_code == 201

    data = response.get_json()
    assert data["status"] == "success"

    driver = Driver.query.filter_by(user_id=user.id).first()
    assert driver is not None
    assert driver.vehicle_brand == "Toyota"

    updated_user = db.session.get(type(user), user.id)
    assert updated_user.role == UserRole.DRIVER

def test_become_driver_custom_exception(client, auth_headers):
    client.post(
        "/driver/becomeDriver",
        json=VALID_DRIVER_DATA,
        headers=auth_headers
    )

    response = client.post(
        "/driver/becomeDriver",
        json=VALID_DRIVER_DATA,
        headers=auth_headers
    )

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"

def test_become_driver_unexpected_exception(client, auth_headers):
    with patch("blueprints.DriverAccess.db.session.commit", side_effect=Exception("DB failure")):
        response = client.post(
            "/driver/becomeDriver",
            json=VALID_DRIVER_DATA,
            headers=auth_headers
        )

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"

def test_become_driver_get_html(client, auth_headers):
    with patch("blueprints.DriverAccess.render_template", return_value="OK"):
        response = client.get(
            "/driver/becomeDriver",
            headers=auth_headers
        )

    assert response.status_code == 200


def test_become_driver_template_missing(client, auth_headers):
    with patch("blueprints.DriverAccess.render_template", side_effect=TemplateNotFound("becomeDriver.html")):
        response = client.get(
            "/driver/becomeDriver",
            headers=auth_headers
        )

    assert response.status_code == 404