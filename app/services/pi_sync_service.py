from PyQt6.QtCore import QObject, pyqtSignal

from app.client.pi_client import PiClient
from app.services.flow_state_coordinator import ProductivityState
from app.utils.log import get_main_app_logger

logger = get_main_app_logger(__name__)

DEFAULT_POMODORO_TIME = 600


class PiSyncService(QObject):
    application_state_changed = pyqtSignal(bool)

    def __init__(self, pi_client: PiClient):
        super().__init__()
        self.pi_client = pi_client
        logger.debug("[INIT] PiSyncService initialization complete")

    def enable(self):
        pass

    def disable(self):
        self.pi_client.pause_all_timers()
        # self.pi_client.wait_for_completion()

    def update_pi_state(self, state: ProductivityState, time: int | None):
        if state == ProductivityState.POMODORO:
            self.pi_client.start_pomodoro_timer(time)
            logger.debug('[API] PI client successfully delivered start pomodoro post request')
        elif state == ProductivityState.PRODUCTIVE:
            self.pi_client.start_productive_timer(time)
            logger.debug('[API] PI client successfully delivered start productive time post request')
        elif state == ProductivityState.NON_PRODUCTIVE:
            self.pi_client.start_non_productive_timer(time)
            logger.debug('[API] PI client successfully delivered start non_productive time post request')
        else:
            self.pi_client.pause_all_timers()
            logger.debug('[API] PI client successfully delivered pause all timers post request')
