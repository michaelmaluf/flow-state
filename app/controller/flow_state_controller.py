from collections import deque

from PyQt6.QtCore import QTimer

from app.domain.models import Application, ApplicationView, Workday
from app.utils.log import get_main_app_logger

logger = get_main_app_logger(__name__)


class FlowStateController:
    def __init__(self, home_view, flow_state_service):
        self.view = home_view
        self.service = flow_state_service

        self.ui_timer = QTimer()
        self.ui_timer.setInterval(60000)
        self.minutes_since_last_reset = 0

        # local variables of archived data
        self.local_productive_time = 0
        self.local_non_productive_time = 0
        self.local_pomodoros_remaining = 0
        self.local_pomodoro_time = 0

        self.current_application = None
        self.is_tracking = False

        self.connect_slots_to_signals()
        self.service.load_todays_workday()

    def on_pomodoro_status_updated(self, time, pomodoros_remaining, elapsed_time):
        self.local_pomodoro_time = time
        self.local_pomodoros_remaining = pomodoros_remaining
        self.view.update_pomodoro_status(time, pomodoros_remaining, True)
        self.ui_timer.setInterval(1000)
        self.minutes_since_last_reset = 0
        self.current_application = None

        # if self.recent_applications:
        #     self.recent_applications[0].elapsed_time = elapsed_time
        #     self.view.update_recent_applications(self.recent_applications)

    def connect_slots_to_signals(self):
        self.ui_timer.timeout.connect(self.update_timers)

        # Connect view signals to controller methods
        self.view.start_app_clicked.connect(self.start_tracking)
        self.view.stop_app_clicked.connect(self.stop_tracking)
        self.view.start_pomodoro_clicked.connect(self.start_pomodoro)
        self.view.end_pomodoro_clicked.connect(self.end_pomodoro)

        # Connect service signals to controller methods
        self.service.application_state_changed.connect(self.on_application_status_changed)
        self.service.new_workday_loaded.connect(self.on_new_workday_loaded)
        self.service.elapsed_time_updated.connect(self.on_elapsed_time_updated)
        self.service.current_application_changed.connect(self.on_current_application_changed)
        self.service.pomodoro_status_updated.connect(self.on_pomodoro_status_updated)

    def on_new_workday_loaded(self, productive_time_seconds, non_productive_time_seconds, pomodoros_left):
        self.local_productive_time = productive_time_seconds
        self.local_non_productive_time = non_productive_time_seconds
        self.local_pomodoros_remaining = pomodoros_left

        self.view.update_productive_time(self.local_productive_time)
        self.view.update_non_productive_time(self.local_non_productive_time)
        self.view.update_pomodoros_remaining(self.local_pomodoros_remaining)

    """
    update UI on interval (1s)
    """

    def update_timers(self):
        if self.local_pomodoro_time:
            self.local_pomodoro_time -= 1
            logger.debug(f"Updating pomodoro time in view to: {self.local_pomodoro_time}s")
            self.view.update_pomodoro_time(self.local_pomodoro_time)
            if self.local_pomodoro_time == 0:
                self.end_pomodoro()
        elif self.current_application:
            seconds_since_last_reset = 60 * self.minutes_since_last_reset
            updated_productive_time = self.local_productive_time
            updated_non_productive_time = self.local_non_productive_time

            if self.current_application.is_productive:
                updated_productive_time += seconds_since_last_reset
            else:
                updated_non_productive_time += seconds_since_last_reset

            logger.debug(f"Updating productive time in view to: {updated_productive_time}s")
            logger.debug(f"Updating non productive time in view to: {updated_non_productive_time}s")
            self.view.update_productive_time(updated_productive_time)
            self.view.update_non_productive_time(updated_non_productive_time)

            self.minutes_since_last_reset += 1


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

    def on_elapsed_time_updated(self, elapsed_time):
        self.view.update_recent_application_time(elapsed_time)

    def on_current_application_changed(self, new_app: Application, workday: Workday):
        logger.info(f"Current application changed to: {new_app.name}")

        if not self.current_application or new_app.is_productive != self.current_application.is_productive:
            logger.info(f"Flow state changed to: {'productive' if new_app.is_productive else 'non-productive'}")

        self.current_application = new_app
        self.local_productive_time = workday.productive_time_seconds
        self.local_non_productive_time = workday.non_productive_time_seconds

        self.ui_timer.stop()
        self.minutes_since_last_reset = 0
        self.update_timers()
        self.ui_timer.start()

        self.view.update_recent_applications(ApplicationView(name=new_app.name, is_productive=new_app.is_productive))
