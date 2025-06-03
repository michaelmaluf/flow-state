from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QTabWidget, QComboBox, QSizePolicy, QScrollArea
)

from app.domain.analytics import AnalyticsReport, TimeFrame
from app.domain.models import ApplicationView
from app.ui.components import PieChart, AppCard


class AnalyticsView(QWidget):
    analytics_report_requested = pyqtSignal(object)
    shutdown_detected = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(50)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        time_analysis_frame = self._create_time_analysis_section()
        breakdown_frame = self._create_breakdown_section()

        main_layout.addWidget(time_analysis_frame, 1)
        main_layout.addWidget(breakdown_frame, 2)

    def showEvent(self, event):
        super().showEvent(event)
        self.tabs.tabBar().setCursor(Qt.CursorShape.PointingHandCursor)

    def closeEvent(self, event):
        # Disconnect before destruction
        self.dropdown.currentIndexChanged.disconnect(self._on_dropdown_index_changed)
        super().closeEvent(event)

    def update_with_analytics_report(self, analytics_report: AnalyticsReport):
        self._update_time_analysis_section(analytics_report)
        self._update_breakdown_section(analytics_report)


    def _create_time_analysis_section(self):
        time_analysis_frame = QFrame()
        time_analysis_frame.setObjectName('timeAnalysisFrame')

        time_analysis_layout = QVBoxLayout(time_analysis_frame)
        time_analysis_layout.setContentsMargins(0, 10, 50, 10)
        time_analysis_layout.setSpacing(15)
        time_analysis_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        time_title = QLabel("Time Analysis")
        time_title.setStyleSheet("font-size: 30px; font-weight: bold; color: #fff;")
        time_analysis_layout.addWidget(time_title, alignment=Qt.AlignmentFlag.AlignCenter)


        # Dropdown menu (styled QComboBox)
        self.dropdown = QComboBox()
        self.dropdown.addItems(["Today       ▼", "This Week      ▼", "This Month     ▼", "All Time     ▼"])
        self.dropdown.setCurrentIndex(0)
        self.dropdown.setStyleSheet("""
            QComboBox {
                background-color: #23263a;
                color: #bfc7d5;
                border: 1.5px solid #35395a;
                border-radius: 8px;
                padding: 6px 24px 6px 12px;
                font-size: 1.1rem;
                min-width: 120px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background: #23263a;
                color: #bfc7d5;
                border-radius: 8px;
                selection-background-color: #35395a;
            }
        """)
        self.dropdown.currentIndexChanged.connect(self._on_dropdown_index_changed)
        time_analysis_layout.addWidget(self.dropdown, alignment=Qt.AlignmentFlag.AlignCenter)

        # Pie chart placeholder
        self.pie_chart = PieChart(productive_percent=65)
        time_analysis_layout.addWidget(self.pie_chart, alignment=Qt.AlignmentFlag.AlignCenter)

        # Productive/Non-Productive summary boxes
        prod_box = QFrame()
        prod_box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        prod_box.setMaximumWidth(250)
        prod_box.setObjectName("prodFrame")
        prod_box.setStyleSheet("""
            #prodFrame {
                background: #182a20; 
                border: 1.5px solid #2ecc71; 
                border-radius: 14px; 
                padding: 0px 50px;
            } 
            #prodFrame QLabel {
                background: transparent;
            } 
            """
        )

        prod_layout = QVBoxLayout(prod_box)
        prod_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        prod_label = QLabel("Productive Time")
        prod_label.setStyleSheet("color: #2ecc71; font-size: 14px; font-weight: bold;")
        prod_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.prod_percent = QLabel("65%")
        self.prod_percent.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prod_percent.setStyleSheet("color: #2ecc71; font-size: 24px; font-weight: bold;")
        self.prod_time = QLabel("5h 12m")
        self.prod_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prod_time.setStyleSheet("color: #a9d2a9; font-size: 1.2rem; font-weight: bold;")

        prod_layout.addWidget(prod_label)
        prod_layout.addWidget(self.prod_percent)
        prod_layout.addWidget(self.prod_time)

        time_analysis_layout.addWidget(prod_box, alignment=Qt.AlignmentFlag.AlignCenter)

        nonprod_box = QFrame()
        nonprod_box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        nonprod_box.setMaximumWidth(250)
        nonprod_box.setObjectName("nonProdFrame")
        nonprod_box.setStyleSheet("""
            #nonProdFrame {
                background: #2a181a; 
                border: 1.5px solid #e74c3c; 
                border-radius: 14px; 
                padding: 0px 35px;
            } 
            #nonProdFrame QLabel {
                background: transparent;
            } 
            """
        )

        nonprod_layout = QVBoxLayout(nonprod_box)
        nonprod_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nonprod_label = QLabel("Non-Productive Time")
        nonprod_label.setStyleSheet("color: #e74c3c; font-size: 14px; font-weight: bold;")
        nonprod_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.nonprod_percent = QLabel("35%")
        self.nonprod_percent.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nonprod_percent.setStyleSheet("color: #e74c3c; font-size: 24px; font-weight: bold;")
        self.nonprod_time = QLabel("2h 48m")
        self.nonprod_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nonprod_time.setStyleSheet("color: #bea9a9; font-size: 1.2rem; font-weight: bold;")


        nonprod_layout.addWidget(nonprod_label)
        nonprod_layout.addWidget(self.nonprod_percent)
        nonprod_layout.addWidget(self.nonprod_time)

        time_analysis_layout.addWidget(nonprod_box, alignment=Qt.AlignmentFlag.AlignCenter)

        # Total tracked label
        self.total_tracked = QLabel("Total Tracked: 8h 0m")
        self.total_tracked.setStyleSheet("color: #bfc7d5; font-size: 14px; margin-top: 12px;")
        time_analysis_layout.addWidget(self.total_tracked, alignment=Qt.AlignmentFlag.AlignCenter)
        time_analysis_layout.addStretch()

        return time_analysis_frame

    def _create_breakdown_section(self):
        breakdown_frame = QFrame()
        breakdown_frame.setObjectName('breakdownFrame')
        breakdown_frame.setStyleSheet("""
            QFrame#breakdownFrame {
                background-color: #20223e;
                border-radius: 32px;
                padding: 32px;
            }
        """)
        breakdown_layout = QVBoxLayout(breakdown_frame)
        breakdown_layout.setSpacing(24)

        # Title
        breakdown_title = QLabel("Application Breakdown")
        breakdown_title.setStyleSheet("font-size: 30px; font-weight: bold; color: #fff; background-color: transparent;")
        breakdown_layout.addWidget(breakdown_title, alignment=Qt.AlignmentFlag.AlignLeft)

        # Tabs for Productive/Non-Productive
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        tab_bar = self.tabs.tabBar()
        tab_bar.setExpanding(False)

        self.tabs.setStyleSheet("""
            QTabBar::tab {
                background: #35395a;
                color: #bfc7d5;
                padding: 12px 32px;
                font-size: 16px;
                font-weight: bold;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #4a69dd;
                color: #fff;
            }
            QTabWidget::tab-bar {
                alignment: left; 
            }
        """)

        prod_tab = self.create_app_list(productive=True)
        nonprod_tab = self.create_app_list(productive=False)

        self.tabs.addTab(prod_tab, "Productive")
        self.tabs.addTab(nonprod_tab, "Non-Productive")
        breakdown_layout.addWidget(self.tabs, 1)

        return breakdown_frame

    def update_app_breakdowns(self, apps: list[ApplicationView], total_time_reference: int, productive=True):
        content_layout = self.prod_content_layout if productive else self.nonprod_content_layout

        while content_layout.count() > 0:
            item = content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for app in apps:
            app_card = AppCard(app.name, app.elapsed_time, int(round(app.elapsed_time / max(1, total_time_reference) * 100)))
            content_layout.addWidget(app_card)

        content_layout.addStretch()

    def create_app_list(self, productive=True):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Style the scroll area
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2a2d42;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #4361ee;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5a79ed;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
                subcontrol-position: none;
            }
            QScrollBar::up-arrow:vertical,
            QScrollBar::down-arrow:vertical {
                width: 0px;
                height: 0px;
                background: none;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        content_widget = QWidget()
        content_widget.setStyleSheet("""
            background-color: #20223e;
        """)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 5, 0, 0)
        content_layout.setSpacing(5)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Sample apps data (make it longer to test scrolling)
        if productive:
            self.prod_content_layout = content_layout
            apps = [
                ApplicationView(name="VS Code", is_productive=True, elapsed_time=2 * 3600 + 30 * 60),
                ApplicationView(name="Terminal", is_productive=True, elapsed_time=1 * 3600 + 15 * 60),
                ApplicationView(name="Docker Desktop", is_productive=True, elapsed_time=45 * 60),
                ApplicationView(name="IntelliJ IDEA", is_productive=True, elapsed_time=1 * 3600 + 5 * 60),
                ApplicationView(name="Figma", is_productive=True, elapsed_time=35 * 60),
                ApplicationView(name="Postman", is_productive=True, elapsed_time=25 * 60),
                ApplicationView(name="GitHub Desktop", is_productive=True, elapsed_time=20 * 60),
                ApplicationView(name="Notion", is_productive=True, elapsed_time=15 * 60),
                ApplicationView(name="Notion", is_productive=True, elapsed_time=15 * 60),
                ApplicationView(name="Notion", is_productive=True, elapsed_time=15 * 60),
                ApplicationView(name="Notion", is_productive=True, elapsed_time=15 * 60),
                ApplicationView(name="Notion", is_productive=True, elapsed_time=15 * 60),
            ]
        else:
            self.nonprod_content_layout = content_layout
            apps = [
                ApplicationView(name="Slack", is_productive=False, elapsed_time=30 * 60),
                ApplicationView(name="Outlook", is_productive=False, elapsed_time=12 * 60),
                ApplicationView(name="Confluence", is_productive=False, elapsed_time=20 * 60),
                ApplicationView(name="Teams", is_productive=False, elapsed_time=18 * 60),
                ApplicationView(name="Twitter", is_productive=False, elapsed_time=25 * 60),
                ApplicationView(name="YouTube", is_productive=False, elapsed_time=40 * 60),
                ApplicationView(name="Reddit", is_productive=False, elapsed_time=15 * 60),
            ]

        self.update_app_breakdowns(apps, productive)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        return main_widget

    def _on_dropdown_index_changed(self, index):
        if index == 0:
            self.analytics_report_requested.emit(TimeFrame.TODAY)
        elif index == 1:
            self.analytics_report_requested.emit(TimeFrame.WEEK)
        elif index == 2:
            self.analytics_report_requested.emit(TimeFrame.MONTH)
        else:
            self.analytics_report_requested.emit(TimeFrame.ALL)

    def _update_time_analysis_section(self, analytics_report):
        overall_time = max(1, analytics_report.overall_time)

        prod_percent = int(round(analytics_report.productive_time / overall_time * 100))
        self.pie_chart.set_data(prod_percent)
        self.prod_percent.setText(f"{prod_percent}%")
        self.prod_time.setText(self._format_time_from_seconds(analytics_report.productive_time))

        nonprod_percent = int(round(analytics_report.non_productive_time / overall_time * 100))
        self.nonprod_percent.setText(f"{nonprod_percent}%")
        self.nonprod_time.setText(self._format_time_from_seconds(analytics_report.non_productive_time))

        self.total_tracked.setText(f"Total Tracked: {self._format_time_from_seconds(overall_time)}")

    def _update_breakdown_section(self, analytics_report):
        self.update_app_breakdowns(analytics_report.productive_time_breakdown, analytics_report.productive_time)
        self.update_app_breakdowns(analytics_report.non_productive_time_breakdown, analytics_report.non_productive_time, productive=False)

    def _format_time_from_seconds(self, seconds: int):
        hours, remainder = divmod(seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours}h {minutes}m" if hours else f"{minutes}m"
