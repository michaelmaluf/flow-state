import datetime
import os
import subprocess
import sys
from collections import defaultdict
from typing import Optional
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from client.claude_client import AIClient
from services.application_tracking_service import ApplicationTrackingService
from services.session_service import SessionService
from domain.accountability_mode import AccountabilityState
from db.database import Database
from domain.models import ScriptResponse, Application, Workday, WorkdayApplication
from log import get_main_app_logger

logger = get_main_app_logger(__name__)

POMODORO_DURATION = 600


class WorkdayService:
    def __init__(self, db: Database, ai_client: AIClient):
        self.db = db
        self.application_tracking_service = ApplicationTrackingService(db, ai_client)
        self.session_service = SessionService(db)
        self.workday = self.load_workday()
        self.pending_applications_to_flush: defaultdict[int, int] = defaultdict(int)
        self.last_flush_time = datetime.datetime.now()
        self.pomodoro_start_time: Optional[datetime.datetime] = None
        self._callback = None

    def set_callback(self, callback_function):
        self._callback = callback_function


    def run_workflow(self):
        script_response = self.run_bash_script()
        logger.debug(f"Bash script response: {script_response}")

        if self.should_skip(script_response):
            if self.should_flush_to_db():
                self.flush_updates_to_db()
            return

        application = self.resolve_application(script_response)
        self.handle_session_transition(application)
        self.handle_application_transition(application, script_response.tag)

    def run_bash_script(self):
        response = ''
        try:
            result = subprocess.run([os.path.join(project_root, "get_current_application.sh")],
                                    capture_output=True,
                                    text=True,
                                    timeout=10)
            response = result.stdout

        except Exception as e:
            logger.error(f"Error running bash script. Bash script timed out: {e}")

        split_response = response.split(':', 2)
        if len(split_response) < 2:
            logger.error(f"Bash script response error, split response < 2: {response}")

        return ScriptResponse.from_arr(*split_response)

    def should_skip(self, script_response: ScriptResponse) -> bool:
        if self.application_tracking_service.is_current_application(script_response):
            logger.debug("Application is current application, skipping workflow")
            return True
        return False

    def resolve_application(self, script_response: ScriptResponse) -> Application:
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

    def handle_session_transition(self, application: Application):
        # If pomodoro is active, do not alter the state of the session, defer until it is completed
        if self.is_pomodoro_active():
            return

        self.session_service.update_session(application)

    def handle_application_transition(self, application: Application, tag: str):
        old_application = self.application_tracking_service.set_current_application(
            application,
            tag=tag,
            start_time=datetime.datetime.now()
        )
        if old_application:
            self.save_workday_application(old_application)

        if self.is_pomodoro_active():
            return

        if old_application is None:
            # First application being tracked
            if application.is_productive:
                self._callback(AccountabilityState.PRODUCTIVE, self.workday.productive_time_seconds)
            else:
                self._callback(AccountabilityState.NON_PRODUCTIVE, self.workday.non_productive_time_seconds)
        elif not old_application.is_productive and application.is_productive:
            # Switching from non-productive to productive
            self._callback(AccountabilityState.PRODUCTIVE, self.workday.productive_time_seconds)
        elif old_application.is_productive and not application.is_productive:
            # Switching from productive to non-productive
            self._callback(AccountabilityState.NON_PRODUCTIVE, self.workday.non_productive_time_seconds)


    def load_workday(self) -> Workday:
        return self.db.load_todays_workday()

    def save_workday_application(self, application: Application):
        duration = int((datetime.datetime.now() - application.start_time).total_seconds())

        self.pending_applications_to_flush[application.id] += duration

        if application.is_productive:
            self.workday.productive_time_seconds += duration
        else:
            self.workday.non_productive_time_seconds += duration

        if len(self.pending_applications_to_flush) >= 5 or self.should_flush_to_db():
            self.flush_updates_to_db()

    def should_flush_to_db(self):
        return datetime.datetime.now() - self.last_flush_time >= datetime.timedelta(minutes=2)

    def flush_updates_to_db(self):
        logger.info(f"Flushing workday and workday_application updates to db")
        self.db.update_workday(self.workday)
        self.flush_applications_to_db()

        self.pending_applications_to_flush.clear()
        self.last_flush_time = datetime.datetime.now()

    def flush_applications_to_db(self):
        if not self.pending_applications_to_flush:
            return

        logger.info(f"Flushing {len(self.pending_applications_to_flush)} application records")

        workday_applications = [
            WorkdayApplication(
                workday_id=self.workday.id,
                application_id=app_id,
                time_seconds=duration
            ) for app_id, duration in self.pending_applications_to_flush.items()
        ]

        self.db.bulk_save_workday_applications(workday_applications)

    def activate_pomodoro(self):
        if self.workday.pomodoros_left == 0:
            return
        self.workday.pomodoros_left -= 1
        self.db.update_workday(self.workday)
        self._callback(AccountabilityState.POMODORO, POMODORO_DURATION)

    def is_pomodoro_active(self):
        if self.pomodoro_start_time and datetime.datetime.now() - self.pomodoro_start_time < datetime.timedelta(seconds=POMODORO_DURATION):
            return True
        return False

    def end_pomodoro(self):
        self.pomodoro_start_time = None
