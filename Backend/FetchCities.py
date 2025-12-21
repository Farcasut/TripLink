from threading import Event, Thread
from pathlib import Path
from typing import Final
import requests
import math

URL: Final[str] = 'https://countriesnow.space/api/v0.1/countries/cities'
GEO_URL: Final[str] = 'https://nominatim.openstreetmap.org/search'
LOCATION_CACHE: dict[str, tuple[float, float]] = dict()
BASE_PATH: Final[Path] = Path('static')
CITY_CACHE: dict[str, list] = dict()
EVENT: Event = Event()

HEADERS: Final[dict] = {
    "Content-Type": "application/json"
}

def _fetch_all(country):
    global URL, HEADERS, EVENT
    payload = {
        "country": country,
    }

    response = requests.post(URL, json = payload, headers = HEADERS)
    CITY_CACHE[country] = response.json()['data']
    EVENT.set()

def get_all(country) -> list:
    # TODO(fix): Should be used with only one country for now.
    global CITY_CACHE, EVENT
    EVENT.wait()
    return CITY_CACHE[country]

def prefetch(country):
    Thread(target = _fetch_all, args=(country,)).start()

def _fetch_location(city, country):
    global GEO_URL
    params = {
        'city': city,
        'country': country,
        'format': 'json',
        'limit': 1
    }

    headers = {
        'User-Agent': 'TripLink-Agent'
    }

    response = requests.get(GEO_URL, params = params, headers = headers)
    response.raise_for_status()
    data = response.json()

    if not data:
        raise ValueError(f'Could not geocode {city} from {country}.')

    return float(data[0]['lat']), float(data[0]['lon'])

CENTROID: Final[tuple[float, float]] = (45.943161, 24.96676)

def get_location(city, country) -> tuple[float, float]:
    global LOCATION_CACHE, CENTROID
    if city in LOCATION_CACHE:
        return LOCATION_CACHE[city]

    try:
        data = _fetch_location(city, country)
        LOCATION_CACHE[city] = data
        return data
    except:
        return CENTROID

def distance(city1: tuple[float, float], city2: tuple[float, float]):
    lat1, lon1 = city1
    lat2, lon2 = city2
    R: Final[float] = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
