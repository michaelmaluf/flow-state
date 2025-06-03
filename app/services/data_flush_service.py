from collections import defaultdict

from PyQt6.QtCore import QObject, QTimer

from app.db.database import Database
from app.domain.models import Application, Workday, WorkdayApplication
from app.utils.log import get_main_app_logger

logger = get_main_app_logger(__name__)

DEFAULT_POMODORO_TIME = 600


class DataFlushService(QObject):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.workday = None
        self.pending_applications_to_flush: defaultdict[Application, int] = defaultdict(int)

        self.flush_timer = QTimer()
        logger.debug("[INIT] DataFlushService initialization complete")

    def connect_slots_to_signals(self):
        self.flush_timer.timeout.connect(self._handle_flush_to_db)

    def enable(self, workday: Workday = None):
        if workday:
            self.workday = workday
        self.flush_timer.start(60000)

    def disable(self):
        self.flush_timer.stop()

    def force_flush(self, application: Application, reactivate: bool):
        logger.info(f"[FLUSH] Processing request to force flush data to database")
        self.flush_timer.stop()
        if application:
            self.pending_applications_to_flush[application] += application.elapsed_time
            application.elapsed_time = 0
        self._handle_flush_to_db()

        self.flush_timer.start() if reactivate else None

    def add_app_to_next_flush(self, application: Application):
        self.pending_applications_to_flush[application] += application.elapsed_time
        logger.debug(f"[FLUSH] {application.name} has been added to the next flush (time: {application.elapsed_time})")

    def _handle_flush_to_db(self):
        logger.info(f"[FLUSH] Flushing workday and {len(self.pending_applications_to_flush)} application records to db")
        try:
            self.db.update_workday(self.workday)
            self._flush_applications_to_db()
            self.pending_applications_to_flush.clear()
            logger.debug("[FLUSH] Successfully flushed data to database")
        except Exception as e:
            logger.error(f"[FLUSH] Failed to flush data to database: {str(e)}")

    def _flush_applications_to_db(self):
        if not self.pending_applications_to_flush:
            return

        try:
            workday_applications = [
                WorkdayApplication(
                    workday_id=self.workday.id,
                    application_id=app.id,
                    time_seconds=duration
                ) for app, duration in self.pending_applications_to_flush.items()
            ]

            for wa in workday_applications:
                logger.debug(f"[FLUSH] workday_id={wa.workday_id}, app_name={wa.application_id}, time={wa.time_seconds}s")

            self.db.bulk_save_workday_applications(workday_applications)
        except Exception as e:
            logger.error(f"[FLUSH] Failed to save workday applications: {str(e)}")
            raise
