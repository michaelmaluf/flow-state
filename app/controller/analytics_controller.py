import uuid

from PyQt6.QtCore import QThreadPool

from app.domain.analytics import TimeFrame, AnalyticsReport
from app.domain.qt_worker import QTWorker
from app.utils.log import get_main_app_logger

logger = get_main_app_logger(__name__)


class AnalyticsController:
    def __init__(self, analytics_view, analytics_service):
        self.view = analytics_view
        self.service = analytics_service
        self.thread_pool = QThreadPool.globalInstance()
        self.current_request_id = None

        self.connect_slots_to_signals()

    def connect_slots_to_signals(self):
        self.view.analytics_report_requested.connect(self.on_analytics_report_requested)

    def on_analytics_report_requested(self, time_frame: TimeFrame):
        analytics_report_id = str(uuid.uuid4())
        self.current_request_id = analytics_report_id

        logger.info(f"Received request to generate analytics report w/ time frame: {time_frame} (Request Id: {analytics_report_id})")

        worker = QTWorker(
            self.service.generate_analytics_report,
            time_frame=time_frame
        )

        # worker.signals.result.connect(lambda result: self.on_data_received(result, analytics_report_id))

        worker.signals.error.connect(self.on_error)
        worker.signals.progress.connect(self.on_progress)
        worker.signals.finished.connect(self.on_request_finished)

        self.thread_pool.start(worker)



    def on_data_received(self, data: AnalyticsReport, request_id: uuid):
        """Called when data is ready - runs in UI thread"""
        logger.info(f"Analytics report successfully generated for time frame: {data.time_frame} (Request Id: {request_id})")
        if request_id == self.current_request_id:
            self.view.update_with_analytics_report(data)
        else:
            logger.debug(f"Ignoring stale result from request {request_id}")

    def on_error(self, error_message):
        """Handle errors"""
        pass
        # self.view.show_error_message(error_message)

    def on_progress(self, n: any):
        """Update ui with progress indicators"""
        pass

    def on_request_finished(self):
        """Called when request completes (success or error)"""
        pass
        # self.view.hide_loading_state()