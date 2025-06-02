import datetime

from PyQt6.QtCore import QObject, pyqtSignal

from app.db.database import Database
from app.domain.models import Workday
from app.utils.log import get_main_app_logger

logger = get_main_app_logger(__name__)

DEFAULT_POMODORO_TIME = 600


class WorkdayService(QObject):
    new_workday_loaded = pyqtSignal(object)
    daily_flush_triggered = pyqtSignal()

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self._workday = None

    @property
    def workday(self):
        if self._workday is None:
            self.load_todays_workday()
        return self._workday

    @workday.setter
    def workday(self, value):
        self._workday = value
        if value:
            self.new_workday_loaded.emit(value)

    def load_todays_workday(self):
        today = datetime.date.today()

        if self._workday and self._workday.date != today:
            # new day, force daily flush and signal new workday
            self.daily_flush_triggered.emit()
            self._workday = None

        self.workday = self.db.get_todays_workday()

    def get_todays_workday(self) -> Workday:
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
