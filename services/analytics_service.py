import datetime
from PyQt6.QtCore import QObject, pyqtSignal
from db.database import Database
from domain.models import ApplicationView
from log import get_main_app_logger
from domain.analytics import TimeFrame, AnalyticsReport

logger = get_main_app_logger(__name__)


class AnalyticsService(QObject):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        logger.debug("AnalyticsService initialization complete")

    def generate_analytics_report(self, time_frame: TimeFrame, progress_callback):
        from_ = datetime.date(2025, 5, 1)

        if time_frame == TimeFrame.TODAY:
            from_ = datetime.date.today() - datetime.timedelta(days=1)
        elif time_frame == TimeFrame.WEEK:
            from_ = datetime.date.today() - datetime.timedelta(days=7)
        elif time_frame == TimeFrame.MONTH:
            from_ = datetime.date.today() - datetime.timedelta(days=30)

        total_productive, total_non_productive = self.db.get_workday_totals_from(from_)

        analytics_report = AnalyticsReport(
            time_frame=time_frame,
            overall_time=total_productive + total_non_productive,
            productive_time=total_productive,
            non_productive_time=total_non_productive
        )

        application_totals = self.db.get_workday_application_totals_from(from_)

        for application in application_totals:
            application_view = ApplicationView(
                name=application.name,
                is_productive=application.is_productive,
                elapsed_time=application.total_time
            )

            if application.is_productive:
                application_view.percent_usage = application.total_time / max(1, total_productive)
                analytics_report.productive_time_breakdown.append(application_view)
            else:
                application_view.percent_usage = application.total_time / max(1, total_non_productive)
                analytics_report.non_productive_time_breakdown.append(application_view)

        return analytics_report
