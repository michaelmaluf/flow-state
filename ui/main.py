import sys

import matplotlib
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget)

from client.claude_client import ClaudeClient
from client.pi_client import PiClient
from controller.flow_state_controller import FlowStateController
from db.database import Database
from log import setup_logging
from services.flow_state_service import FlowStateService
from ui.views.analytics_view import AnalyticsView
from ui.views.home_view import HomeView

matplotlib.use('Qt5Agg')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('FlowState')
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e2130;
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
                background-color: #2d3142;
                border-radius: 10px;
            }
        """)

        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Create tabs
        self.home_tab = HomeView()
        self.analytics_tab = AnalyticsView()

        # Add tabs to widget
        self.tabs.addTab(self.home_tab, "Home")
        self.tabs.addTab(self.analytics_tab, "Analytics")

        # Set the central widget
        self.setCentralWidget(self.tabs)


if __name__ == '__main__':
    setup_logging()
    app = QApplication([])
    window = MainWindow()

    db = Database("postgresql://percules:***REMOVED***@localhost:5432/flow_state")
    pi_client = PiClient("http://192.168.1.28:5050")
    ai_client = ClaudeClient()
    flow_state_service = FlowStateService(db, ai_client, pi_client)

    flow_state_controller = FlowStateController(window.home_tab, flow_state_service)

    window.show()
    sys.exit(app.exec())
