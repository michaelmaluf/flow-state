from app.domain.models import Application, ApplicationView, Workday
from app.services.flow_state_coordinator import ProductivityState
from app.utils.log import get_main_app_logger

logger = get_main_app_logger(__name__)


class FlowStateController:
    def __init__(self, home_view, flow_state_coordinator):
        self.view = home_view
        self.service = flow_state_coordinator
        self.is_tracking = False
        self.connect_slots_to_signals()

    def connect_slots_to_signals(self):
        # Connect view signals to controller methods
        self.view.start_app_clicked.connect(self.start_tracking)
        self.view.stop_app_clicked.connect(self.stop_tracking)
        self.view.start_pomodoro_clicked.connect(self.start_pomodoro)
        self.view.end_pomodoro_clicked.connect(self.end_pomodoro)
        self.view.request_initial_data.connect(self.on_request_initial_data)

        # Connect service signals to controller methods
        self.service.application_status_changed.connect(self.on_application_status_changed)
        self.service.workday_loaded.connect(self.on_new_workday_loaded)
        self.service.timer_updated.connect(self.on_timer_updated)
        self.service.pomodoro_state_changed.connect(self.on_pomodoro_state_changed)
        self.service.current_application_changed.connect(self.on_current_application_changed)

    """
    handlers for view events, calls methods in tracking service
    """
    def start_tracking(self):
        logger.info("[USER_ACTION] Start application button clicked")
        self.is_tracking = True
        self.service.start_tracking()

    def stop_tracking(self):
        logger.info("[USER_ACTION] Stop application button clicked")
        if not self.is_tracking:
            return

        self.is_tracking = False
        self.service.stop_tracking()

    def start_pomodoro(self):
        logger.info("[USER_ACTION] Start pomodoro button clicked")
        self.service.start_pomodoro()

    def end_pomodoro(self):
        logger.info("[USER_ACTION] End pomodoro button clicked")
        if self.is_tracking:
            self.service.end_pomodoro()

    def on_request_initial_data(self):
        self.service.load_workday()


    """
    handlers for tracking service events, calls methods to update view
    """
    def on_application_status_changed(self, is_tracking):
        logger.debug(f"[SERVICE_EVENT] Application tracking state changed to: {is_tracking}")
        self.view.update_application_status(is_tracking)

    def on_new_workday_loaded(self, workday: Workday):
        logger.debug(f"[SERVICE_EVENT] Loading new workday data for date: {workday.date}")
        self.view.update_productive_time(workday.productive_time_seconds, 0)
        self.view.update_non_productive_time(workday.non_productive_time_seconds, 0)
        self.view.update_pomodoros_remaining(workday.pomodoros_left)

    def on_timer_updated(self, state: ProductivityState, total_time: int, current_app_time: int):
        if state == ProductivityState.PRODUCTIVE:
            self.view.update_productive_time(total_time, current_app_time)
        elif state == ProductivityState.NON_PRODUCTIVE:
            self.view.update_non_productive_time(total_time, current_app_time)
        elif state == ProductivityState.POMODORO:
            self.view.update_pomodoro_time(total_time)

    def on_pomodoro_state_changed(self, time, pomodoros_remaining, is_active):
        self.view.update_pomodoro_status(time, pomodoros_remaining, is_active)

    def on_current_application_changed(self, new_app: Application):
        logger.debug(f"[SERVICE_EVENT] Current application changed to: {new_app.name}")
        self.view.update_recent_applications(ApplicationView(name=new_app.name, is_productive=new_app.is_productive))
