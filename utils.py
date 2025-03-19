import time
import random
import datetime as dt
import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import List, Dict, Any, Tuple, Optional, Set

import requests

import config as c


_DATA: Dict[str, List[Dict[str, Any]]] = {}
_TIMESTAMP: dt.datetime = dt.datetime(1453, 5, 29)
_LOCK = Lock()

def _fetch_data(url: str) -> List[Dict[str, Any]]:
    logging.info(f"Fetching data from: {url}")
    for i in range(3):  
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching data from {url}: {e}")
            time.sleep(2**i + random.random())

    logging.error(f"Failed to fetch data from {url} after 3 attempts")
    return []
    

def _fetch_launchpads() -> List[Dict[str, Any]]:
    """
    Fetch launchpad data from the SpaceX API.
    """
    launchpads = _fetch_data(f"{c.SPACEX_BASE_URL}/launchpads")

    # get interesting fields from launchpads
    return [
        {
            "id": launchpad.get("id"),
            "name": launchpad.get("name"),
            "status": launchpad.get("status"),
            "rockets": launchpad.get("rockets"),
            "launches": launchpad.get("launches"),
        }
        for launchpad in launchpads
    ]

def _fetch_rockets() -> List[Dict[str, Any]]:
    """
    Fetch rocket data from the SpaceX API.
    """
    rockets = _fetch_data(f"{c.SPACEX_BASE_URL}/rockets")

    # get interesting fields from rockets
    return [
        {
            "id": rocket.get("id"),
            "name": rocket.get("name"),
            "active": rocket.get("active"),
        }
        for rocket in rockets
    ]

def _fetch_launches() -> List[Dict[str, Any]]:
    """
    Fetch launch data from the SpaceX API.
    """
    launches = _fetch_data(f"{c.SPACEX_BASE_URL}/launches")

    # get interesting fields from launches
    return [
        {
            "id": launch.get("id"),
            "name": launch.get("name"),
            "launchpad": launch.get("launchpad"),
            "date_utc": launch.get("date_utc"),
            "success": launch.get("success"),
            "rocket": launch.get("rocket"),
        }
        for launch in launches
    ]

def fetch_data() -> Tuple[List[Dict[str, Any]], bool]:
    """
    Return data from the API endpoint, using a cache to minimize API calls.
    """
    global _DATA, _TIMESTAMP

    def __foo(key: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Fetch data from the API endpoint.
        """
        if key == "launches":
            data = _fetch_launches()
        elif key == "rockets":
            data = _fetch_rockets()
        elif key == "launchpads":
            data = _fetch_launchpads()
        else:
            data = []
        return (key, data)

    with _LOCK:
        # first check cache (if expired or missing, fetch from API)
        if _TIMESTAMP.timestamp() - dt.datetime.now().timestamp() < c.CACHE_EXPIRY and _DATA:
            return _DATA, False
            
        # If cache is expired or missing, fetch from API and save cache.
        logging.info(f"Fetching data...")
        with ThreadPoolExecutor(max_workers=3) as executor:
            data = dict(executor.map(__foo, ["launches", "rockets", "launchpads"]))

        notify_subscribers = len(_DATA.get("launches", [])) != len(data["launches"])
        
        if data:
            _DATA = data
            _TIMESTAMP = dt.datetime.now()

        return data, notify_subscribers

def parse_date(date_str: str | dt.datetime) -> Optional[dt.datetime]:
    """
    Parse a date string into a datetime object.
    """
    for data_formats in [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d"
    ]:
        try:
            return dt.datetime.strptime(date_str, data_formats).replace(tzinfo=dt.timezone.utc)
        except Exception:
            pass
    
    logging.warning(f"Invalid date format: {date_str}")
    return None

def send_notifications(subscribers: Set[str]) -> None:
    """
    Send notifications to subscribers.
    """
    def __foo(subscriber: str) -> None:
        logging.info(f"Sending notification to {subscriber}")
        for i in range(3):
            response = requests.post(subscriber, 
                                     json={"message": "New data is available!"},
                                     timeout=5)
            if response.status_code == 200:
                break
            time.sleep(2**i + random.random())

    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(__foo, subscribers)
