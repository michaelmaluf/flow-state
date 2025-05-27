import atexit
import os
import json
import sys
from pathlib import Path
import signal

import yaml
from PyQt6.QtWidgets import QApplication

from app.controller.analytics_controller import AnalyticsController
from app.services.analytics_service import AnalyticsService
from app.client.pi_client import PiClient
from app.controller.flow_state_controller import FlowStateController
from app.services.flow_state_service import FlowStateService
from app.ui.main import MainWindow
from app.db.database import Database
from app.utils.log import setup_logging, get_main_app_logger
from app.client.claude_client import ClaudeClient
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
            config = yaml.safe_load(f)

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
    flow_state_service = FlowStateService(db, ai_client, pi_client)
    flow_state_controller = FlowStateController(window.home_tab, flow_state_service)

    analytics_service = AnalyticsService(db)
    analytics_controller = AnalyticsController(window.analytics_tab, analytics_service)


def signal_handler(signum, frame):
    logger.info(f"Signal {signum} detected, initiating graceful exit")
    window.handle_graceful_exit()


def exit_handler():
    logger.info("Python exit detected, initiating graceful exit")
    window.handle_graceful_exit()


if __name__ == '__main__':
    create_app()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(exit_handler)

    window.show()
    sys.exit(app.exec())
