import atexit
import os
import signal
import sys

import yaml
from PyQt6.QtWidgets import QApplication

from app.client.claude_client import ClaudeClient
from app.client.pi_client import PiClient
from app.controller.analytics_controller import AnalyticsController
from app.controller.flow_state_controller import FlowStateController
from app.db.database import Database
from app.services.analytics_service import AnalyticsService
from app.services.app_tracking.app_service import AppService
from app.services.data_flush_service import DataFlushService
from app.services.flow_state_coordinator import FlowStateCoordinator
from app.services.pi_sync_service import PiSyncService
from app.services.workday.pomodoro_service import PomodoroService
from app.services.workday.workday_service import WorkdayService
from app.ui.main import MainWindow
from app.utils.log import setup_logging, get_main_app_logger
from app.utils.resolve_path import get_config_path

setup_logging()
logger = get_main_app_logger(__name__)

app: QApplication | None = None
window: MainWindow | None = None
flow_state_controller: FlowStateController | None = None
analytics_controller: AnalyticsController | None = None


def get_config():
    try:
        config_path = get_config_path('config.yaml')

        with open(config_path) as f:
            yaml_content = f.read()

        # Expand environment variables
        expanded_content = os.path.expandvars(yaml_content)

        # Parse the expanded YAML
        config = yaml.safe_load(expanded_content)

        return config
    except Exception as e:
        print(f"Config error: {e}")
        return None


def create_app():
    global app, window, flow_state_controller, analytics_controller

    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow()

    config = get_config()
    db_url = config['database_url']
    ai_api_key = config['ai_api_key']

    db = Database(db_url)

    pi_client = PiClient("http://192.168.1.28:5050")
    ai_client = ClaudeClient(ai_api_key)

    workday_service = WorkdayService(db)
    app_service = AppService(db, ai_client)
    pomodoro_service = PomodoroService()
    data_flush_service = DataFlushService(db)
    pi_sync_service = PiSyncService(pi_client)

    flow_state_coordinator = FlowStateCoordinator(
        workday_service=workday_service,
        app_service=app_service,
        pomodoro_service=pomodoro_service,
        data_flush_service=data_flush_service,
        pi_sync_service=pi_sync_service
    )
    flow_state_controller = FlowStateController(window.home_tab, flow_state_coordinator)

    analytics_service = AnalyticsService(db)
    analytics_controller = AnalyticsController(window.analytics_tab, analytics_service)


def signal_handler(signum, frame):
    logger.info(f"[SYSTEM] Signal {signum} detected, initiating graceful exit")
    window.handle_graceful_exit()
    logger.info("[SYSTEM] Graceful exit completed")


def exit_handler():
    logger.info("[SYSTEM] Python exit detected, initiating graceful exit")
    window.handle_graceful_exit()
    logger.info("[SYSTEM] Graceful exit completed")


if __name__ == '__main__':
    create_app()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(exit_handler)

    window.show()
    sys.exit(app.exec())
