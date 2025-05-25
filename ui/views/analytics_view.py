from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QTabWidget, QTabBar, QGridLayout, QComboBox
)
from PyQt6.QtCore import Qt


class AnalyticsView(QWidget):

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(100)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Left: Time Analysis (1/3)
        time_analysis_frame = self._create_time_analysis_section()
        # Right: Application Breakdown (2/3)
        breakdown_frame = self._create_breakdown_section()

        main_layout.addWidget(time_analysis_frame, stretch=1)
        main_layout.addWidget(breakdown_frame, stretch=2)

    def _create_time_analysis_section(self):
        time_analysis_frame = QFrame()
        time_analysis_frame.setObjectName('timeAnalysisFrame')
        # time_analysis_frame.setStyleSheet("""
        #     QFrame#timeAnalysisFrame {
        #         background-color: #23263a;
        #         border-radius: 32px;
        #         padding: 32px;
        #     }
        # """)
        time_analysis_frame.setMinimumWidth(340)
        time_analysis_frame.setMaximumWidth(380)
        time_analysis_layout = QVBoxLayout(time_analysis_frame)
        time_analysis_layout.setSpacing(24)
        time_analysis_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        time_title = QLabel("Time Analysis")
        time_title.setStyleSheet("font-size: 30px; font-weight: bold; color: #fff;")
        time_analysis_layout.addWidget(time_title, alignment=Qt.AlignmentFlag.AlignLeft)

        # Dropdown menu (styled QComboBox)
        dropdown = QComboBox()
        dropdown.addItems(["Today", "This Week", "This Month"])
        dropdown.setCurrentIndex(0)
        dropdown.setStyleSheet("""
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
            QComboBox::down-arrow {
                image: url(:/qt-project.org/styles/commonstyle/images/arrowdown-16.png);
                width: 16px;
                height: 16px;
            }
            QComboBox QAbstractItemView {
                background: #23263a;
                color: #bfc7d5;
                border-radius: 8px;
                selection-background-color: #35395a;
            }
        """)
        time_analysis_layout.addWidget(dropdown, alignment=Qt.AlignmentFlag.AlignLeft)

        # Pie chart placeholder
        pie_chart = QLabel("[Pie Chart]")
        pie_chart.setFixedSize(220, 220)
        pie_chart.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pie_chart.setStyleSheet("background: #181a20; border-radius: 110px; color: #fff; font-size: 1.2rem;")
        time_analysis_layout.addWidget(pie_chart, alignment=Qt.AlignmentFlag.AlignCenter)

        # Productive/Non-Productive summary boxes
        prod_box = QFrame()
        prod_box.setObjectName("prodFrame")
        prod_box.setStyleSheet("""
            #prodFrame {
                background: #182a20; 
                border: 1.5px solid #2ecc71; 
                border-radius: 14px; 
                padding: 16px;
            } 
            #prodFrame QLabel {
                background: transparent;
            } 
            """
        )

        prod_layout = QVBoxLayout(prod_box)
        prod_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        prod_label = QLabel("Productive Time")
        prod_label.setStyleSheet("color: #2ecc71; font-size: 1.2rem; font-weight: bold;")
        prod_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.prod_percent = QLabel("65%")
        self.prod_percent.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prod_percent.setStyleSheet("color: #2ecc71; font-size: 1.2rem; font-weight: bold;")
        self.prod_time = QLabel("5h 12m")
        self.prod_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prod_time.setStyleSheet("color: #2ecc71; font-size: 1.2rem; font-weight: bold;")

        prod_layout.addWidget(prod_label)
        prod_layout.addWidget(self.prod_percent)
        prod_layout.addWidget(self.prod_time)

        time_analysis_layout.addWidget(prod_box)

        nonprod_box = QFrame()
        nonprod_box.setObjectName("nonProdFrame")
        nonprod_box.setStyleSheet("""
            #nonProdFrame {
                background: #2a181a; 
                border: 1.5px solid #e74c3c; 
                border-radius: 14px; 
                padding: 16px;
            } 
            #nonProdFrame QLabel {
                background: transparent;
            } 
            """
        )

        nonprod_layout = QVBoxLayout(nonprod_box)
        nonprod_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nonprod_label = QLabel("Non-Productive Time")
        nonprod_label.setStyleSheet("color: #e74c3c; font-size: 1.2rem; font-weight: bold;")
        nonprod_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.nonprod_percent = QLabel("35%")
        self.nonprod_percent.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nonprod_percent.setStyleSheet("color: #e74c3c; font-size: 1.2rem; font-weight: bold;")
        self.nonprod_time = QLabel("2h 48m")
        self.nonprod_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nonprod_time.setStyleSheet("color: #e74c3c; font-size: 1.2rem; font-weight: bold;")


        nonprod_layout.addWidget(nonprod_label, alignment=Qt.AlignmentFlag.AlignCenter)
        nonprod_layout.addWidget(self.nonprod_percent)
        nonprod_layout.addWidget(self.nonprod_time)

        time_analysis_layout.addWidget(nonprod_box)

        # Total tracked label
        total_tracked = QLabel("Total Tracked: 8h 0m")
        total_tracked.setStyleSheet("color: #bfc7d5; font-size: 1rem; margin-top: 12px;")
        time_analysis_layout.addWidget(total_tracked, alignment=Qt.AlignmentFlag.AlignCenter)
        time_analysis_layout.addStretch()

        return time_analysis_frame

    def _create_breakdown_section(self):
        breakdown_frame = QFrame()
        breakdown_frame.setObjectName('breakdownFrame')
        breakdown_frame.setStyleSheet("""
            QFrame#breakdownFrame {
                background-color: #23263a;
                border-radius: 32px;
                padding: 32px;
            }
        """)
        breakdown_layout = QVBoxLayout(breakdown_frame)
        breakdown_layout.setSpacing(24)

        # Title
        breakdown_title = QLabel("Application Breakdown")
        breakdown_title.setStyleSheet("font-size: 2rem; font-weight: bold; color: #fff;")
        breakdown_layout.addWidget(breakdown_title, alignment=Qt.AlignmentFlag.AlignLeft)

        # Tabs for Productive/Non-Productive
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North)
        tabs.setStyleSheet("""
            QTabBar::tab {
                background: #35395a;
                color: #bfc7d5;
                padding: 12px 32px;
                font-size: 1.1rem;
                font-weight: bold;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #4a69dd;
                color: #fff;
            }
        """)
        prod_tab = QWidget()
        nonprod_tab = QWidget()
        tabs.addTab(prod_tab, "Productive")
        tabs.addTab(nonprod_tab, "Non-Productive")
        breakdown_layout.addWidget(tabs)

        # Productive tab content (list of apps)
        prod_tab_layout = QVBoxLayout(prod_tab)
        for app, time, percent in [
            ("VS Code", "2h 30m", "48%"),
            ("Terminal", "1h 15m", "24%"),
            ("Docker Desktop", "45m", "15%"),
            ("Slack", "30m", "10%"),
            ("Outlook", "12m", "3%"),
            ("Confluence", "20m", "6%"),
        ]:
            app_row = QFrame()
            app_row.setStyleSheet("background: #35395a; border-radius: 12px; padding: 12px 24px;")
            row_layout = QHBoxLayout(app_row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(0)
            app_label = QLabel(app)
            app_label.setStyleSheet("color: #fff; font-size: 1.1rem;")
            time_label = QLabel(f"{time} ({percent})")
            time_label.setStyleSheet("color: #bfc7d5; font-size: 1.1rem;")
            row_layout.addWidget(app_label)
            row_layout.addStretch()
            row_layout.addWidget(time_label)
            prod_tab_layout.addWidget(app_row)
        prod_tab_layout.addStretch()

        # Non-Productive tab content (empty for now)
        nonprod_tab_layout = QVBoxLayout(nonprod_tab)
        nonprod_tab_layout.addStretch()

        return breakdown_frame
