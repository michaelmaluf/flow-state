from PyQt6.QtCore import QObject, pyqtSignal, QTimer, Qt

from app.domain.enums import FlowStateStatus, ProductivityState
from app.domain.models import Application, Workday
from app.services.app_tracking.app_service import AppService
from app.services.data_flush_service import DataFlushService
from app.services.pi_sync_service import PiSyncService
from app.services.workday.pomodoro_service import PomodoroService
from app.services.workday.workday_service import WorkdayService
from app.utils.log import get_main_app_logger

logger = get_main_app_logger(__name__)


class FlowStateCoordinator(QObject):
    application_status_changed = pyqtSignal(bool)
    workday_loaded = pyqtSignal(object)
    timer_updated = pyqtSignal(object, int, int)  # (state, total time, current app time if applicable)
    pomodoro_state_changed = pyqtSignal(int, int, bool)
    current_application_changed = pyqtSignal(object)

    def __init__(
            self,
            workday_service: WorkdayService,
            app_service: AppService,
            pomodoro_service: PomodoroService,
            data_flush_service: DataFlushService,
            pi_sync_service: PiSyncService
    ):
        super().__init__()
        self.workday_service = workday_service
        self.app_service = app_service
        self.pomodoro_service = pomodoro_service
        self.data_flush_service = data_flush_service
        self.pi_sync_service = pi_sync_service

        self.status = FlowStateStatus.INACTIVE
        self.state = ProductivityState.IDLE

        self.sync_timer = QTimer()

        self.connect_slots_to_signals()

    def connect_slots_to_signals(self):
        self.app_service.current_application_changed.connect(self._handle_new_app)
        self.workday_service.new_workday_loaded.connect(self._on_new_workday_loaded)
        self.workday_service.daily_flush_triggered.connect(self._force_data_flush, Qt.ConnectionType.DirectConnection)
        self.pomodoro_service.pomodoro_completed.connect(self.end_pomodoro)
        self.sync_timer.timeout.connect(self._handle_sync_update)

    def start_tracking(self):
        if self.status == FlowStateStatus.INACTIVE:
            self.status = FlowStateStatus.ACTIVE
            self.app_service.enable()
            self.data_flush_service.enable(self.workday_service.get_todays_workday())
            self.sync_timer.start(1000)
            self.application_status_changed.emit(True)
        else:
            logger.warning("Attempted to start tracking while already tracking")

    def stop_tracking(self):
        if self.status == FlowStateStatus.ACTIVE:
            self.status = FlowStateStatus.SHUTDOWN
            self.sync_timer.stop()
            self._update_state(ProductivityState.IDLE)

            self.app_service.disable()
            self._force_data_flush()
            self.data_flush_service.disable()
            self.pi_sync_service.disable()

            self.application_status_changed.emit(False)
            self.status = FlowStateStatus.INACTIVE
        else:
            logger.warning("Attempted to stop tracking while not tracking")

    def load_workday(self):
        self.workday_service.load_todays_workday()

    def _on_new_workday_loaded(self, workday: Workday):
        self.workday_loaded.emit(workday)

    def _pause_tracking(self):
        if self.status == FlowStateStatus.ACTIVE:
            self.app_service.disable()
            self._force_data_flush()
            self.data_flush_service.disable()

        else:
            logger.warning("Attempted to pause tracking while not tracking")

    def _resume_tracking(self):
        if self.status == FlowStateStatus.ACTIVE:
            self.app_service.enable()
            self.data_flush_service.enable(self.workday_service.get_todays_workday())
        else:
            logger.warning("Attempted to resume tracking while not tracking")

    def start_pomodoro(self):
        pomodoros_remaining = self.workday_service.use_pomodoro_if_available()

        if pomodoros_remaining == -1:
            logger.warning("Attempted to start pomodoro with no pomodoros remaining")
            return

        self.sync_timer.stop()
        self._pause_tracking()
        self.pomodoro_service.start_pomodoro()
        self._update_state(ProductivityState.POMODORO)
        self.pomodoro_state_changed.emit(self.pomodoro_service.pomodoro_time, pomodoros_remaining, True)
        self.sync_timer.start()

        logger.info(f"Starting pomodoro. Remaining: {pomodoros_remaining}")

    def end_pomodoro(self):
        if self.pomodoro_service.pomodoro_active:
            self.pomodoro_service.cancel_pomodoro()

        self.sync_timer.stop()
        self._resume_tracking()
        self.pomodoro_state_changed.emit(0, 0, False)
        self.sync_timer.start()

    def _handle_new_app(self, old_app: Application, new_app: Application):
        # if old app -> save to flush service to be flushed
        if old_app:
            self.data_flush_service.add_app_to_next_flush(old_app)

        expected_state = ProductivityState.PRODUCTIVE if new_app.is_productive else ProductivityState.NON_PRODUCTIVE
        if self.state != expected_state:
            self._update_state(expected_state)

        self.current_application_changed.emit(new_app)

    def _update_state(self, state: ProductivityState):
        time = 0
        if state == ProductivityState.PRODUCTIVE:
            time = self.workday_service.get_productive_time()
        elif state == ProductivityState.NON_PRODUCTIVE:
            time = self.workday_service.get_non_productive_time()
        elif state == ProductivityState.POMODORO:
            time = self.pomodoro_service.pomodoro_time
        else:
            # idle state requested, if currently in pomodoro then end pomodoro
            if self.state == ProductivityState.POMODORO:
                self.pomodoro_service.cancel_pomodoro()
                self.pomodoro_state_changed.emit(0, 0, False)

        self.pi_sync_service.update_pi_state(state, time)
        self.state = state

    def _handle_sync_update(self):
        if self.state == ProductivityState.POMODORO:
            pomodoro_time_remaining = self.pomodoro_service.decrement_pomodoro_time()
            if pomodoro_time_remaining >= 0:
                self.timer_updated.emit(self.state, pomodoro_time_remaining, -1)
        else:
            is_productive = True if self.state == ProductivityState.PRODUCTIVE else False
            workday_updated_time = self.workday_service.increment_workday_time(1, is_productive)
            application_updated_time = self.app_service.increment_application_time(1)
            self.timer_updated.emit(self.state, workday_updated_time, application_updated_time)

    def _force_data_flush(self):
        current_application = self.app_service.get_current_application()
        self.data_flush_service.force_flush(current_application)
        current_application.elapsed_time = 0
