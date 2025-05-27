from PyQt6.QtCore import pyqtSlot, QRunnable, QObject, pyqtSignal

from app.client.claude_client import AIClient
from app.db.database import Database
from app.domain.models import ScriptResponse, Application
from app.utils.log import get_main_app_logger

logger = get_main_app_logger(__name__)


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(float)


class AppProcessingService(QRunnable):
    class Signals(QObject):
        finished = pyqtSignal()
        error = pyqtSignal(tuple)
        result = pyqtSignal(object)
        progress = pyqtSignal(float)

    def __init__(self, db: Database, ai_client: AIClient, script_response: ScriptResponse):
        super().__init__()
        self.db = db
        self.ai_client = ai_client
        self.script_response = script_response
        self.signals = self.Signals()

    @pyqtSlot()
    def run(self):
        """
        1. CASE 1: tag workflow, needs ai intervention
        2. CASE 2: desktop app or web app in database, return
        3. CASE 3: new desktop app or web app, add to db workflow
        """
        app = self.get_application(self.script_response.app_name)
        if self.script_response.tag:
            app = self.process_tag_workflow(self.script_response.app_name, self.script_response.tag)
        elif not app:
            app = self.process_new_application(self.script_response.app_type, self.script_response.app_name)

        self.signals.result.emit(app)

    def get_application(self, app_name: str) -> Application:
        return self.db.get_application(app_name)

    def get_or_create_application(self, app_name: str, is_productive: bool = False) -> Application:
        return self.db.get_or_create_application(app_name, is_productive)


    def process_new_application(self, app_type: str, app_name: str) -> Application:
        if app_type == 'APP':
            is_productive = True
        else:
            claude_inquiry = self.format_web_app_inquiry(app_name)
            response = self.ai_client.send_message(claude_inquiry)
            is_productive = (response == 'True' or response == 'true')

        return self.db.create_application(app_name, is_productive)

    def process_tag_workflow(self, app_name: str, msg: str) -> Application:
        """
        tag workflows -> any workflows where intervention via AI client is needed to determine productivity
        example: youtube videos, subreddits, etc
        """
        formatted_msg = ''

        if app_name == 'youtube':
            formatted_msg = self.format_yt_video_inquiry(msg)
        elif app_name == 'reddit':
            formatted_msg = self.format_subreddit_inquiry(msg)
        else:
            logger.error(f"App name not valid for tag workflow: {app_name}")

        is_productive = self.ai_client.send_message(formatted_msg).lower() == 'true'
        return self.get_or_create_application(app_name, is_productive)

    def format_web_app_inquiry(self, app_name: str):
        return (
                f"Is this web application likely to be productive or non-productive content? " +
                f"Answer with exactly one word, either 'True' for productive or 'False' for non-productive: {app_name}"
        )

    def format_yt_video_inquiry(self, yt_video_title: str):
        return (
                f"Is this YouTube video title likely to be productive or non-productive content? " +
                f"Answer with exactly one word, either 'True' for productive or 'False' for non-productive: {yt_video_title}"
        )

    def format_subreddit_inquiry(self, subreddit_name: str):
        return (
                f"Is this subreddit likely to be productive or non-productive content? " +
                f"Answer with exactly one word, either 'True' for productive or 'False' for non-productive: {subreddit_name}"
        )
