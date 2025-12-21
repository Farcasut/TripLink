from threading import Event, Thread
from pathlib import Path
from typing import Final
import requests

URL: Final[str] = 'https://countriesnow.space/api/v0.1/countries/cities'
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
