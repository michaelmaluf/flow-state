import os
import sys
import requests as requests
from requests.exceptions import RequestException, Timeout, HTTPError
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from log import get_main_app_logger


logger = get_main_app_logger(__name__)

class PiClient:
    def __init__(self, url: str, timeout: int = 5):
        self.base_url = url
        self.timeout = timeout

    def _post(self, endpoint: str, payload: dict = None):
        url = f"{self.base_url}/flow-state/{endpoint}"
        try:
            response = requests.post(url, json=payload or {}, timeout=self.timeout)
            response.raise_for_status()
        except Timeout:
            logger.error(f"Request to {url} timed out.")
        except HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code} for {url}: {e.response.text}")
        except RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
        except ValueError:
            logger.error(f"Failed to decode JSON from {url}")
        except Exception:
            logger.exception(f"Unexpected error while calling {url}")

    def start_productive_timer(self, time: int):
        return self._post("productive", {"time": time})

    def start_non_productive_timer(self, time: int):
        return self._post("non-productive", {"time": time})

    def start_pomodoro_timer(self, time: int):
        return self._post("pomodoro", {"time": time})
