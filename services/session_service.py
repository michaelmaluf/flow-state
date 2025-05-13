import datetime
import os
import sys
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import Database
from domain.models import Application, Session
from log import get_main_app_logger

logger = get_main_app_logger(__name__)

class SessionService:
    def __init__(self, db: Database):
        self.db = db
        self.current_session: Optional[Session] = None

    def update_session(self, application: Application):
        now = datetime.datetime.now()
        logger.debug(f"Updating session based on application: {application.name} (productive: {application.is_productive})")

        # Case 1: No change needed - app status matches session status
        if self._should_continue_current_session(application):
            self._continue_current_session()
        # Case 2: Start new session - productive app with no session
        elif self._should_start_new_session(application):
            self._start_new_session(application, now)
        # Case 3: Non-productive app + session, determine if session should end
        elif self._should_end_current_session(application, now):
            self._end_current_session(now)

    def _should_continue_current_session(self, application: Application) -> bool:
        return (not application.is_productive and not self.current_session) or \
            (application.is_productive and self.current_session)

    def _continue_current_session(self):
        if self.current_session:
            logger.debug("Continuing current productive session, clearing idle time")
            self.current_session.idle_time = None
        else:
            logger.debug("No session active, non-productive app, no action needed")

    def _should_start_new_session(self, application: Application) -> bool:
        return application.is_productive and not self.current_session

    def _start_new_session(self, application: Application, now: datetime.datetime):
        logger.info(f"Starting new productive session for app: {application.name}")
        self.current_session = Session(
            start_time=now
        )

    def _should_end_current_session(self, application: Application, now: datetime.datetime) -> bool:
        if not application.is_productive and self.current_session:
            self.current_session.interruption_count += 1
            logger.debug(f"Session interrupted, count: {self.current_session.interruption_count}")

            if not self.current_session.idle_time and self.current_session.interruption_count < 10:
                logger.debug("Starting idle time tracking, continuing session")
                self.current_session.idle_time = now
                return False

            if self.current_session.idle_time and (now - self.current_session.idle_time) < datetime.timedelta(minutes=2):
                logger.debug("Within short idle period, continuing session")
                return False

            return True
        return False

    def _end_current_session(self, now: datetime.datetime):
        idle_duration = (now - self.current_session.idle_time).total_seconds() if self.current_session.idle_time else 0
        duration = (now - self.current_session.start_time).total_seconds()

        logger.info(
            f"Ending session, duration: {duration}s, interruptions: {self.current_session.interruption_count}, idle: {idle_duration}s")

        self.current_session.end_time = now
        self.db.save_session(self.current_session)
        self.current_session = None
