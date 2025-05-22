import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.base_network_client import BaseNetworkClient
from log import get_main_app_logger

logger = get_main_app_logger(__name__)


class PiClient(BaseNetworkClient):
    def __init__(self, url: str):
        super().__init__(url)
        self.base_url = url

    def _handle_success(self, operation_type, response):
        logger.info(f"Successful HTTP request to pi client (Operation Type: {operation_type}, Response: {response})")
        self.response_received.emit(operation_type, response)

    def _handle_error(self, operation_type, error_msg, status_code):
        error_detail = f"{operation_type} failed: {error_msg}"
        if status_code:
            error_detail += f" (HTTP {status_code})"

        logger.error(f"Failed HTTP request to pi client (Operation Type: {operation_type}, Error Details: {error_detail})")
        self.request_error.emit(operation_type, error_detail)

    def start_productive_timer(self, time: int):
        payload = {"time": time}
        self.post('/flow-state/productive', payload, 'start_productive_timer')

    def start_non_productive_timer(self, time: int):
        payload = {"time": time}
        self.post('/flow-state/non-productive', payload, 'start_non_productive_timer')

    def start_pomodoro_timer(self, time: int):
        payload = {"time": time}
        self.post('/flow-state/pomodoro', payload, 'start_pomodoro_timer')

    def pause_all_timers(self):
        self.post('/flow-state/pause', None, 'pause_all_timers')
