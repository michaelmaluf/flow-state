import atexit
import os
import sys
import signal
from PyQt6.QtWidgets import QApplication

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.pi_client import PiClient
from controller.flow_state_controller import FlowStateController
from services.flow_state_service import FlowStateService
from ui.main import MainWindow
from db.database import Database
from log import setup_logging, get_main_app_logger
from client.claude_client import ClaudeClient

setup_logging()
logger = get_main_app_logger(__name__)

app: QApplication | None = None
window: MainWindow | None = None
flow_state_controller: FlowStateController | None = None

# TODO: fix ui somehow lol, look into making this a desktop application AND THEN look into completing analytics tab
# TODO: test that times and flushes and workflow is working, appears to be running smoothly but test for the day

def create_app():
    global app, window, flow_state_controller

    app = QApplication([])
    window = MainWindow()

    db = Database(f"postgresql://percules:{sys.argv[1]}@localhost:5432/flow_state")
    pi_client = PiClient("http://192.168.1.28:5050")
    ai_client = ClaudeClient(sys.argv[2])
    flow_state_service = FlowStateService(db, ai_client, pi_client)
    flow_state_controller = FlowStateController(window.home_tab, flow_state_service)


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
