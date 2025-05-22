from collections import deque

from PyQt6.QtCore import QTimer

from domain.models import Application, ApplicationView
from log import get_main_app_logger

logger = get_main_app_logger(__name__)


class FlowStateController:
    def __init__(self, home_view, flow_state_service):
        self.view = home_view
        self.service = flow_state_service

        self.ui_timer = QTimer()
        self.ui_timer.setInterval(60000)

        # local variables of archived data
        self.local_productive_time = 0
        self.local_non_productive_time = 0
        self.local_pomodoros_remaining = 0
        self.local_pomodoro_time = 0

        self.current_application = None
        self.recent_applications: deque[ApplicationView] = deque()
        self.is_tracking = False

        self.connect_slots_to_signals()
        self.init_local_variables()

    def on_pomodoro_status_updated(self, time, pomodoros_remaining):
        self.local_pomodoro_time = time
        self.local_pomodoros_remaining = pomodoros_remaining
        self.view.update_pomodoro_status(time, pomodoros_remaining, True)
        self.ui_timer.setInterval(1000)

    def connect_slots_to_signals(self):
        self.ui_timer.timeout.connect(self.update_timers)

        # Connect view signals to controller methods
        self.view.start_app_clicked.connect(self.start_tracking)
        self.view.stop_app_clicked.connect(self.stop_tracking)
        self.view.start_pomodoro_clicked.connect(self.start_pomodoro)
        self.view.end_pomodoro_clicked.connect(self.end_pomodoro)

        # Connect service signals to controller methods
        self.service.application_state_changed.connect(self.on_application_status_changed)
        self.service.current_application_changed.connect(self.on_current_application_changed)
        self.service.pomodoro_status_updated.connect(self.on_pomodoro_status_updated)

    def init_local_variables(self):
        current_workday = self.service.get_current_workday()
        self.local_productive_time = current_workday.productive_time_seconds
        self.local_non_productive_time = current_workday.non_productive_time_seconds
        self.local_pomodoros_remaining = current_workday.pomodoros_left

        self.view.update_productive_time(self.local_productive_time)
        self.view.update_non_productive_time(self.local_non_productive_time)

    """
    update UI on interval (1s)
    """

    def update_timers(self):
        if self.local_pomodoro_time:
            self.local_pomodoro_time -= 1
            self.view.update_pomodoro_time(self.local_pomodoro_time)
        elif not self.current_application:
            return
        elif self.current_application.is_productive:
            self.local_productive_time += 1
            self.view.update_productive_time(self.local_productive_time)
        else:
            self.local_non_productive_time += 1
            self.view.update_non_productive_time(self.local_non_productive_time)

    """
    handlers for view events, calls methods in tracking service
    """

    def start_tracking(self):
        logger.info("Starting application tracking")
        self.is_tracking = True
        self.service.start_tracking()
        self.ui_timer.start()

    def stop_tracking(self):
        logger.info("Stopping application tracking")
        if not self.is_tracking:
            return

        self.is_tracking = False
        self.service.stop_tracking()

        if self.local_pomodoro_time:
            self.end_pomodoro()
        self.ui_timer.stop()

    def start_pomodoro(self):
        logger.info("Starting pomodoro timer")
        self.service.start_pomodoro()

    def end_pomodoro(self):
        logger.info("Ending pomodoro timer")
        self.local_pomodoro_time = 0
        self.ui_timer.setInterval(60000)
        if self.is_tracking:
            self.service.end_pomodoro()
        self.view.update_pomodoro_status(0, self.local_pomodoros_remaining)

    """
    handlers for tracking service events, calls methods to update view
    """

    def on_application_status_changed(self, is_tracking):
        logger.info(f"Application tracking state changed to: {is_tracking}")
        self.view.update_application_status(is_tracking)

    def on_current_application_changed(self, new_app: Application, elapsed_time: int):
        logger.info(f"Current application changed to: {new_app.name}")

        if self.recent_applications:
            self.recent_applications[0].elapsed_time = elapsed_time

        if not self.current_application or new_app.is_productive != self.current_application.is_productive:
            logger.info(f"Flow state changed to: {'productive' if new_app.is_productive else 'non-productive'}")
            # self.view.update_application_state(application.is_productive)
            # update current state (p, np, pomo)
            # MIGHT NOT NEED THIS AT ALL, HAVE A SLOT ABOVE THAT INCREMENTS TIME AND VIEW DECIPHERS STATE OFF THAT

        self.current_application = new_app

        if len(self.recent_applications) >= 4:
            self.recent_applications.pop()

        self.recent_applications.appendleft(ApplicationView(name=new_app.name, is_productive=new_app.is_productive))
        self.view.update_recent_applications(self.recent_applications)

    # def on_productive_time_updated(self, time: int):
    #     self.view.update_productive_time(time)
    #
    # def on_non_productive_time_updated(self, time: int):
    #     self.view.update_productive_time(time)

    # def on_pomodoro_time_updated(self, time: int):
    #     self.view.update_pomodoro_time(time)
    #
    # def on_pomodoros_remaining_updated(self, count: int):
    #     self.view.update_pomodoros_remaining(count)
