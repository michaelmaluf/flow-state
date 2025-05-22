import datetime
from collections import defaultdict

from PyQt6.QtCore import QObject, pyqtSignal, QThreadPool, QTimer

from client.claude_client import AIClient
from client.pi_client import PiClient
from db.database import Database
from domain.models import ScriptResponse, Application, Workday, WorkdayApplication
from log import get_main_app_logger
from services.app_monitor_service import AppMonitorService
from services.app_processing_service import AppProcessingService

logger = get_main_app_logger(__name__)

DEFAULT_POMODORO_TIME = 600


class FlowStateService(QObject):
    application_state_changed = pyqtSignal(bool)
    current_application_changed = pyqtSignal(object, int)
    pomodoro_status_updated = pyqtSignal(int, int)
    recent_apps_changed = pyqtSignal(list)  # (name, productive bool, time) for last 3 apps

    def __init__(self, db: Database, ai_client: AIClient, pi_client: PiClient):
        super().__init__()
        self.db = db
        self.ai_client = ai_client
        self.pi_client = pi_client

        self.app_monitor = AppMonitorService()
        self.is_tracking = False
        self.threadpool = QThreadPool()

        self.workday = self.db.get_todays_workday()
        self.current_application = None
        self.pending_applications_to_flush: defaultdict[Application, int] = defaultdict(int)

        self.flush_timer = QTimer()
        self.flush_timer.setInterval(15000)

        self.connect_slots_to_signals()
        logger.debug("FlowStateService initialization complete")

    def connect_slots_to_signals(self):
        self.app_monitor.new_script_response.connect(self._handle_new_script_response)
        self.flush_timer.timeout.connect(self._handle_flush_to_db)

    def start_tracking(self):
        if not self.is_tracking:
            self.is_tracking = True
            self.app_monitor.start()
            self.flush_timer.start()
            self.application_state_changed.emit(True)
        else:
            logger.warning("Attempted to start tracking while already tracking")

    def stop_tracking(self):
        if self.is_tracking:
            self.is_tracking = False

            # Stop thread properly
            self.app_monitor.stop()

            # manual flush
            self.flush_timer.stop()
            self._handle_flush_to_db(finalize_current_app=self.current_application is not None)

            self.current_application = None
            self.pi_client.pause_all_timers()
            self.pi_client.wait_for_completion()

            self.application_state_changed.emit(False)
        else:
            logger.warning("Attempted to stop tracking while not tracking")

    def get_current_workday(self) -> Workday:
        return self.workday

    def start_pomodoro(self):
        if self.workday.pomodoros_left <= 0:
            logger.warning("Attempted to start pomodoro with no pomodoros remaining")
            return

        self.app_monitor.pause()  # pause application tracking during pomodoro

        # Flush to DB on pomodoro, by doing this we update workday and application state so we can come back to a fresh slate on completion
        self.workday.pomodoros_left -= 1
        self.flush_timer.stop()
        self._handle_flush_to_db(finalize_current_app=self.current_application is not None)
        self.flush_timer.start()

        logger.info(f"Starting pomodoro. Remaining: {self.workday.pomodoros_left}")

        self._update_pi_state('pomodoro')
        self.current_application = None
        self.pomodoro_status_updated.emit(DEFAULT_POMODORO_TIME, self.workday.pomodoros_left)


    def end_pomodoro(self):
        self.app_monitor.resume()


    def _update_pi_state(self, state):
        if state == 'pomodoro':
            self.pi_client.start_pomodoro_timer(DEFAULT_POMODORO_TIME)
            logger.debug('PI client successfully delivered start pomodoro post request')
        elif state == 'productive':
            self.pi_client.start_productive_timer(self.workday.productive_time_seconds)
            logger.debug('PI client successfully delivered start productive time post request')
        elif state == 'non_productive':
            self.pi_client.start_non_productive_timer(self.workday.non_productive_time_seconds)
            logger.debug('PI client successfully delivered start non_productive time post request')
        else:
            logger.warning(f"Attempted to update pi with illegal state: {state}")


    def _handle_new_script_response(self, script_response: ScriptResponse):
        logger.debug(f"Received new script response for application: {script_response.app_name}")
        worker = AppProcessingService(self.db, self.ai_client, script_response)
        worker.signals.result.connect(self._handle_app_change)
        self.threadpool.start(worker)

    def _handle_app_change(self, new_app: Application):
        duration = 0

        if self.current_application:
            self._finalize_app_time()
            logger.debug(f"Application change: {self.current_application.name} -> {new_app.name}")

        if self.current_application is None or self.current_application.is_productive != new_app.is_productive:
            state = 'productive' if new_app.is_productive else 'non_productive'
            self._update_pi_state(state)

        self.current_application_changed.emit(new_app, duration)
        self.current_application = new_app


    def _finalize_app_time(self):
        duration = int((datetime.datetime.now() - self.current_application.start_time).total_seconds())
        logger.debug(f"Finalized app time for {self.current_application} (duration: {duration}s)")

        self.pending_applications_to_flush[self.current_application] += duration

        if self.current_application.is_productive:
            self.workday.productive_time_seconds += duration
        else:
            self.workday.non_productive_time_seconds += duration

    def _handle_flush_to_db(self, finalize_current_app=False):
        if finalize_current_app:
            self._finalize_app_time()

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

            self.db.bulk_save_workday_applications(workday_applications)
        except Exception as e:
            logger.error(f"Failed to save workday applications: {str(e)}")
            raise
