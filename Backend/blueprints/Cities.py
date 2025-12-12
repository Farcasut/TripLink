from flask import Blueprint, request, jsonify, current_app, abort
import FetchCities

cities = Blueprint("cities", __name__, url_prefix="/cities")

@cities.get('/<string:country>')
def get_cities(country: str):
    try:
        return jsonify({
            'status': 'success',
            'content': FetchCities.get_all(country)
        })
    except Exception:
        return jsonify({
            'status': 'error',
            'content': []
        })
