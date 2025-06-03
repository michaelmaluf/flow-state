from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget)

from app.domain.analytics import TimeFrame
from app.ui.views.analytics_view import AnalyticsView
from app.ui.views.home_view import HomeView
from app.utils.log import get_main_app_logger

logger = get_main_app_logger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        QApplication.instance().applicationStateChanged.connect(self._on_app_state_changed)

    def initUI(self):
        self.setWindowTitle('FlowState')
        self.setGeometry(100, 100, 1200, 800)
        self.setContentsMargins(80, 20, 80, 80)
        self.setObjectName("mainWindow")
        self.setStyleSheet("""
            QMainWindow {
                background-color: #171620;
            }

            QTabWidget::pane {
                border: none;
                background-color: #1e2130;
                
            }
            QTabBar::tab {
                background-color: #2d3142;
                color: white;
                padding: 15px 100px;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 1em;
            }
            QTabBar::tab:selected {
                background-color: #4a69dd;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #4a69dd;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 16px;
            }
            QPushButton:disabled {
                background-color: #2d3142;
            }
            QPushButton:hover {
                background-color: #5a79ed;
            }
            QPushButton:pressed {
                background-color: #3a59cd;
            }
            QPushButton#cancelButton {
                background-color: #3d4155;
            }
            QPushButton#cancelButton:hover {
                background-color: #4d5165;
            }
            QFrame {
                background-color: #171620;
                border-radius: 10px;
                text-align: center;
            }
        """)

        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setContentsMargins(0, 0, 0, 100)

        # Create tabs
        self.home_tab = HomeView()
        self.analytics_tab = AnalyticsView()

        # Add tabs to widget
        self.tabs.addTab(self.home_tab, "Home")
        self.tabs.addTab(self.analytics_tab, "Analytics")

        # Set the central widget
        self.setCentralWidget(self.tabs)

        self.home_tab.request_updated_daily_report.connect(lambda: self.analytics_tab.analytics_report_requested.emit(TimeFrame.TODAY))

    def closeEvent(self, event):
        '''
        method will be overridden when application is transformed into a full-fledged desktop app, most likely will call window.hide() here
        self.hide()
        event.ignore()
        '''
        event.ignore()
        self.hide()

    def showEvent(self, event):
        super().showEvent(event)
        self.tabs.tabBar().setCursor(Qt.CursorShape.PointingHandCursor)
        self.home_tab.request_initial_data.emit()
        self.analytics_tab.analytics_report_requested.emit(TimeFrame.TODAY)

    def handle_graceful_exit(self):
        self.home_tab.stop_app_clicked.emit()
        self.analytics_tab.shutdown_detected.emit()
        QApplication.instance().quit()

    def _on_app_state_changed(self, state):
        if state == Qt.ApplicationState.ApplicationActive:
            if self.isHidden():
                self.show()
                self.raise_()
                self.activateWindow()
