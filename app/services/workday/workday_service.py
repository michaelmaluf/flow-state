import datetime

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from app.db.database import Database
from app.domain.models import Workday
from app.utils.log import get_main_app_logger

logger = get_main_app_logger(__name__)

class WorkdayService(QObject):
    new_workday_loaded = pyqtSignal(object)
    daily_flush_triggered = pyqtSignal()

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self._workday = None
        self._daily_flush_timer = None
        logger.debug("[INIT] WorkdayService initialization complete")

    @property
    def workday(self):
        if self._workday is None or self._workday.date != datetime.date.today():
            self.load_todays_workday()
        return self._workday

    def load_todays_workday(self):
        if self._workday and self._workday.date != datetime.date.today():
            logger.info("[WORKDAY] New workday detected, triggering daily flush for old workday and loading new workday")
            self.daily_flush_triggered.emit()

        self._workday = self.db.get_todays_workday()
        self._set_daily_flush_timer()
        self.new_workday_loaded.emit(self._workday)
        logger.info("[WORKDAY] New workday successfully loaded")

    def get_todays_workday(self) -> Workday:
        self._set_daily_flush_timer()
        return self.workday

    def increment_workday_time(self, elapsed_time: int, is_productive: bool) -> int:
        if is_productive:
            self.workday.productive_time_seconds += elapsed_time
            return self.workday.productive_time_seconds
        else:
            self.workday.non_productive_time_seconds += elapsed_time
            return self.workday.non_productive_time_seconds

    def get_productive_time(self):
        return self.workday.productive_time_seconds

    def get_non_productive_time(self):
        return self.workday.non_productive_time_seconds

    def use_pomodoro_if_available(self) -> int:
        if self.workday.pomodoros_left <= 0:
            return -1
        self.workday.pomodoros_left -= 1
        return self.workday.pomodoros_left

    def _set_daily_flush_timer(self):
        if self._daily_flush_timer is not None:
            self._daily_flush_timer.stop()
            self._daily_flush_timer = None

        now = datetime.datetime.now()
        midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_until_midnight = int((midnight - now).total_seconds()) + 1  # Add 1 second buffer

        self._daily_flush_timer = QTimer()
        self._daily_flush_timer.setSingleShot(True)
        self._daily_flush_timer.timeout.connect(self.load_todays_workday)
        self._daily_flush_timer.start(seconds_until_midnight * 1000)

        logger.info(f"[SYNC] Midnight reset timer set for workday and will go off in: {seconds_until_midnight} seconds")