import datetime
import uuid

from PyQt6.QtCore import QObject, pyqtSignal, QThreadPool

from app.db.database import Database
from app.domain.analytics import TimeFrame, AnalyticsReport
from app.domain.models import ApplicationView
from app.domain.qt_worker import QTWorker
from app.utils.log import get_main_app_logger

logger = get_main_app_logger(__name__)


class AnalyticsService(QObject):
    report_generated = pyqtSignal(object, str)  # result, request_id
    generation_error = pyqtSignal(str, str)  # error_message, request_id
    generation_progress = pyqtSignal(int, str)  # progress_percent, request_id
    generation_finished = pyqtSignal(str)

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.thread_pool = QThreadPool.globalInstance()
        logger.debug("[INIT] AnalyticsService initialization complete")

    def request_analytics_report(self, time_frame: TimeFrame, analytics_report_id: uuid.uuid4()):
        worker = QTWorker(
            self._generate_analytics_report,
            time_frame=time_frame
        )

        # Connect worker signals to service methods
        worker.signals.result.connect(
            lambda result: self.report_generated.emit(result, analytics_report_id)
        )
        worker.signals.error.connect(
            lambda error: self.generation_error.emit(str(error), analytics_report_id)
        )
        worker.signals.progress.connect(
            lambda progress: self.generation_progress.emit(progress, analytics_report_id)
        )
        worker.signals.finished.connect(
            lambda: self.generation_finished.emit(analytics_report_id)
        )

        logger.debug(f"[ANALYTICS] Worker thread spinning up to generate analytics report (id: {analytics_report_id})")

        self.thread_pool.start(worker)

    def _generate_analytics_report(self, time_frame: TimeFrame, progress_callback):
        logger.debug(f"[ANALYTICS] Generating analytics report for time frame: {time_frame}")

        from_ = datetime.date(2025, 5, 31)

        if time_frame == TimeFrame.TODAY:
            from_ = datetime.date.today()
        elif time_frame == TimeFrame.WEEK:
            from_ = datetime.date.today() - datetime.timedelta(days=6)
        elif time_frame == TimeFrame.MONTH:
            from_ = datetime.date.today() - datetime.timedelta(days=29)

        total_productive = 0
        total_non_productive = 0
        productive_apps = []
        non_productive_apps = []

        aggregated_workday_applications = self.db.get_workday_application_totals_from(from_)

        for workday_application in aggregated_workday_applications:
            application_view = ApplicationView(
                name=workday_application.name,
                is_productive=workday_application.is_productive,
                elapsed_time=workday_application.total_time
            )

            if workday_application.is_productive:
                total_productive += workday_application.total_time
                productive_apps.append(application_view)
            else:
                total_non_productive += workday_application.total_time
                non_productive_apps.append(application_view)

        for app_view in productive_apps:
            app_view.percent_usage = app_view.elapsed_time / max(1, total_productive)

        for app_view in non_productive_apps:
            app_view.percent_usage = app_view.elapsed_time / max(1, total_non_productive)

        analytics_report = AnalyticsReport(
            time_frame=time_frame,
            overall_time=total_productive + total_non_productive,
            productive_time=total_productive,
            non_productive_time=total_non_productive,
            productive_time_breakdown=productive_apps,
            non_productive_time_breakdown=non_productive_apps
        )

        logger.debug(f"[ANALYTICS] Analytics report generation completed for time frame: {time_frame}")

        return analytics_report
