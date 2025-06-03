from PyQt6.QtCore import QObject, pyqtSignal, QThreadPool

from app.client.claude_client import AIClient
from app.db.database import Database
from app.domain.models import ScriptResponse, Application
from app.services.app_tracking.app_monitor_service import AppMonitorService
from app.services.app_tracking.app_processing_service import AppProcessingService
from app.utils.log import get_main_app_logger

logger = get_main_app_logger(__name__)

DEFAULT_POMODORO_TIME = 600


class AppService(QObject):
    current_application_changed = pyqtSignal(object, object)  # old app, new app

    def __init__(self, db: Database, ai_client: AIClient):
        super().__init__()
        self.db = db
        self.ai_client = ai_client

        self.app_monitor = AppMonitorService()
        self.threadpool = QThreadPool.globalInstance()
        self.current_application = None

        self.connect_slots_to_signals()

        logger.debug("[INIT] AppService initialization complete")

    def enable(self):
        self.app_monitor.start()
        logger.debug("[TRACKING] App monitor enabled")

    def disable(self):
        self.app_monitor.stop()
        logger.debug("[TRACKING] App monitor disabled")

    def connect_slots_to_signals(self):
        self.app_monitor.new_script_response.connect(self._handle_new_script_response)

    def get_current_application(self):
        return self.current_application

    def _handle_new_script_response(self, script_response: ScriptResponse):
        logger.debug(f"[TRACKING] Received new script response for application: {script_response.app_name}, spinning up App Processing Service")
        worker = AppProcessingService(self.db, self.ai_client, script_response)
        worker.signals.result.connect(self._handle_app_change)
        self.threadpool.start(worker)

    def _handle_app_change(self, new_app: Application):
        logger.debug(f"[TRACKING] Received new application from App Processing Service for script")
        self.current_application_changed.emit(self.current_application, new_app)
        self.current_application = new_app

    def increment_application_time(self, elapsed_time: int) -> int:
        if not self.current_application:
            logger.error(f"[SYNC] Cannot increment application time b/c current application is not set")
        self.current_application.elapsed_time += elapsed_time
        return self.current_application.elapsed_time
