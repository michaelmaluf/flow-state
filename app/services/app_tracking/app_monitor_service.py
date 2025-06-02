import subprocess
import time

from PyQt6.QtCore import QThread, pyqtSignal

from app.domain.models import ScriptResponse
from app.utils.log import get_main_app_logger
from app.utils.resolve_path import get_script_path

logger = get_main_app_logger(__name__)


class AppMonitorService(QThread):
    new_script_response = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.running = False
        self.paused = False
        self.script_path = get_script_path('get_current_application.sh')
        self.last_script_response = None

    def stop(self):
        self.running = False
        self.last_script_response = None
        self.requestInterruption()
        self.wait(1000)

    def pause(self):
        logger.info("App Monitor has been paused, not collecting active application")
        self.paused = True
        self.last_script_response = None

    def resume(self):
        logger.info("App Monitor has been resumed, collecting active application")
        self.paused = False

    def run(self):
        self.running = True
        while self.running and not self.isInterruptionRequested():
            try:
                if not self.paused:
                    script_response = self.get_active_app()
                    if script_response != self.last_script_response:
                        self.new_script_response.emit(script_response)
                        self.last_script_response = script_response

                # Run on a 2-second interval
                time.sleep(2)

            except Exception as e:
                logger.error(f"Error while monitoring current application: {e}")
                time.sleep(5)

    def get_active_app(self):
        """Get the currently active application using bash script"""
        try:
            # Run the bash script
            result = subprocess.run([self.script_path],
                                    capture_output=True,
                                    text=True,
                                    timeout=7)

            if result.returncode != 0:
                raise Exception(f"Script error, bash script returned status code: {result.returncode}")

            # Process the output
            response = result.stdout.strip()
            split_response = response.split(':', 2)

            if len(split_response) < 2:
                raise Exception(f"Bash script response error, split response < 2: {response}")

            return ScriptResponse.from_arr(*split_response)

        except subprocess.TimeoutExpired as e:
            logger.error(f"Script timed out while running: {e}")
            raise
        except Exception:
            raise

