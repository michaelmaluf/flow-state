import os
import sys
from time import sleep

from services.workday_service import WorkdayService

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import Database
from log import setup_logging, get_main_app_logger
from claude_client import ClaudeClient

logger = get_main_app_logger(__name__)





class AccountabilityMode:
    def __init__(self, workday_service: WorkdayService):
        self.workday_service = workday_service

    def run(self):
        self.workday_service.run_workflow()




if __name__ == '__main__':
    setup_logging()
    logger = get_main_app_logger(__name__)

    db = Database("postgresql://percules:***REMOVED***@localhost:5432/flow_state")
    workday_service = WorkdayService(db, ClaudeClient())

    am = AccountabilityMode(workday_service)
    while True:
        am.run()
        sleep(2)
