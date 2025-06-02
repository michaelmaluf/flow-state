from collections import defaultdict

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from app.db.database import Database
from app.domain.models import Application, Workday, WorkdayApplication
from app.utils.log import get_main_app_logger

logger = get_main_app_logger(__name__)

DEFAULT_POMODORO_TIME = 600


class DataFlushService(QObject):
    application_state_changed = pyqtSignal(bool)

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.workday = None
        self.pending_applications_to_flush: defaultdict[Application, int] = defaultdict(int)

        self.flush_timer = QTimer()

    def connect_slots_to_signals(self):
        self.flush_timer.timeout.connect(self._handle_flush_to_db)

    def enable(self, workday: Workday):
        self.workday = workday
        self.flush_timer.start(60000)

    def disable(self):
        self.flush_timer.stop()

    def force_flush(self, application: Application = None):
        self.flush_timer.stop()
        if application:
            self.pending_applications_to_flush[application] += application.elapsed_time
        self._handle_flush_to_db()
        self.flush_timer.start()

    def add_app_to_next_flush(self, application: Application):
        self.pending_applications_to_flush[application] += application.elapsed_time

    def _handle_flush_to_db(self):
        logger.info(f"Flushing workday and {len(self.pending_applications_to_flush)} application records to db")
        try:
            self.db.update_workday(self.workday)
            self._flush_applications_to_db()
            self.pending_applications_to_flush.clear()
            logger.debug("Successfully flushed data to database")
        except Exception as e:
            logger.error(f"Failed to flush data to database: {str(e)}")

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

            logger.info(f"{len(workday_applications)} workday applications to flush to db:")

            for wa in workday_applications:
                logger.info(f"workday_id={wa.workday_id}, app_name={wa.application_id}, time={wa.time_seconds}s")

            self.db.bulk_save_workday_applications(workday_applications)
        except Exception as e:
            logger.error(f"Failed to save workday applications: {str(e)}")
            raise