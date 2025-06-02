from PyQt6.QtCore import QObject, pyqtSignal

from app.utils.log import get_main_app_logger

logger = get_main_app_logger(__name__)

DEFAULT_POMODORO_TIME = 600


class PomodoroService(QObject):
    pomodoro_completed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.pomodoro_active = False
        self.pomodoro_time = 0

    def start_pomodoro(self):
        self.pomodoro_active = True
        self.pomodoro_time = DEFAULT_POMODORO_TIME

    def cancel_pomodoro(self):
        self.pomodoro_active = False
        self.pomodoro_time = 0

    def decrement_pomodoro_time(self):
        if self.pomodoro_time == 0:
            self._complete_pomodoro()
            return -1
        self.pomodoro_time -= 1
        return self.pomodoro_time

    def _complete_pomodoro(self):
        self.pomodoro_active = False
        self.pomodoro_completed.emit()