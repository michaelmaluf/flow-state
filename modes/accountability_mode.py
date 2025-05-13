import datetime
import os
import subprocess
import sys
from time import sleep

from services.application_tracking_service import ApplicationTrackingService
from services.session_service import SessionService

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from db.database import Database
from domain.models import Application, ScriptResponse
from log import setup_logging, get_main_app_logger
from claude_client import AIClient, ClaudeClient

logger = get_main_app_logger(__name__)

# project_dir = os.path.dirname(os.path.abspath(__file__))
# bash_script_path = os.path.join(project_dir, "../get_current_application.sh")




class AccountabilityMode:
    def __init__(self, db: Database, ai_client: AIClient):
        self.application_tracking_service = ApplicationTrackingService(db, ai_client)
        self.session_service = SessionService(db)
        self.bash_script_path = os.path.join(project_root, "get_current_application.sh")

    def run(self):
        script_response: ScriptResponse = self.run_bash_script()
        logger.debug(f"Bash script response: {script_response}")

        if self.application_tracking_service.is_current_application(script_response):
            logger.debug(f"Application is current application, returning")
            return

        application = self.process_script_result(script_response)
        self.session_service.update_session(application)
        self.application_tracking_service.set_current_application(
            application,
            tag=script_response.tag,
            start_time=datetime.datetime.now()
        )

    def run_bash_script(self):
        response = ''
        try:
            result = subprocess.run([self.bash_script_path],
                                    capture_output=True,
                                    text=True,
                                    timeout=10)
            response = result.stdout

        except subprocess.TimeoutExpired as e:
            logger.error("Error running bash script. Bash script timed out")

        split_response = response.split(':', 2)
        if len(split_response) < 2:
            logger.error(f"Bash script response error, split response < 2: {response}")

        return ScriptResponse.from_arr(*split_response)


    def process_script_result(self, script_response: ScriptResponse) -> Application:
        """
        1. CASE 1: tag workflow, needs ai intervention
        2. CASE 2: desktop app or web app in database, return
        3. CASE 3: new desktop app or web app, add to db workflow
        """
        if script_response.tag:
            return self.application_tracking_service.process_tag_workflow(
                script_response.app_name, script_response.tag
            )

        app = self.application_tracking_service.get_application(script_response.app_name)
        if app:
            return app

        return self.application_tracking_service.process_new_application(
            script_response.app_type, script_response.app_name
        )


if __name__ == '__main__':
    setup_logging()
    logger = get_main_app_logger(__name__)

    db = Database("postgresql://percules:***REMOVED***@localhost:5432/flow_state")
    ai_client = ClaudeClient()
    am = AccountabilityMode(db, ai_client)
    while True:
        am.run()
        sleep(2)
