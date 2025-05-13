import datetime
import os
import sys
from typing import Optional

from claude_client import AIClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import Database
from domain.models import ScriptResponse, Application
from log import get_main_app_logger

logger = get_main_app_logger(__name__)


class ApplicationTrackingService:
    def __init__(self, db: Database, ai_client: AIClient):
        self.db = db
        self.ai_client = ai_client
        self.current_application: Optional[Application] = None

    def is_current_application(self, script_response: ScriptResponse) -> bool:
        if self.current_application and self.current_application.is_match(script_response.app_name, script_response.tag):
            logger.debug(f"Running application matches current application: {self.current_application}")
            return True
        return False

    def set_current_application(self, application: Application, **kwargs) -> Application:
        # save stats before setting new current application
        # TODO: save stats, maybe batch stats, record current workday stats, think about how to manage workday
        # entity so it can be used and referenced here
        old_application = self.current_application

        for key, value in kwargs.items():
            setattr(application, key, value)
        self.current_application = application

        return old_application

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

        if app_name == 'Youtube':
            formatted_msg = self.format_yt_video_inquiry(msg)
        elif app_name == 'Reddit':
            formatted_msg = self.format_subreddit_inquiry(msg)
        else:
            logger.error("App name not youtube or reddit, cannot process yt or reddit")

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
