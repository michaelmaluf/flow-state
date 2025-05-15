import os
import sys
from time import sleep
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.pi_client import PiClient
from domain.accountability_mode import AccountabilityState
from services.workday_service import WorkdayService
from db.database import Database
from log import setup_logging, get_main_app_logger
from client.claude_client import ClaudeClient

logger = get_main_app_logger(__name__)

class AccountabilityMode:
    def __init__(self, workday_service: WorkdayService, pi_client: PiClient):
        self.workday_service = workday_service
        self.pi_client = pi_client
        self.workday_service.set_callback(self.send_message_to_pi)
        # self.state: Optional[AccountabilityState] = None

    def run(self):
        self.workday_service.run_workflow()

    def send_message_to_pi(self, state: AccountabilityState, time: int):
        if state == AccountabilityState.PRODUCTIVE:
            self.pi_client.start_productive_timer(time)
        elif state == AccountabilityState.NON_PRODUCTIVE:
            self.pi_client.start_non_productive_timer(time)
        elif state == AccountabilityState.POMODORO:
            self.pi_client.start_pomodoro_timer(time)

        # self.state = state





if __name__ == '__main__':
    setup_logging()
    logger = get_main_app_logger(__name__)

    db = Database("postgresql://percules:***REMOVED***@localhost:5432/flow_state")
    workday_service = WorkdayService(db, ClaudeClient())
    pi_client = PiClient("http://192.168.1.28:5050")

    am = AccountabilityMode(workday_service, pi_client)
    while True:
        am.run()
        sleep(2)
