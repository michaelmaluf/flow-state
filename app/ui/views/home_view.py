from PyQt6.QtCore import (
    pyqtSignal, Qt,
)
from PyQt6.QtWidgets import (
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFrame, QHBoxLayout, QGridLayout
)

from app.domain.models import ApplicationView
from app.ui.components import AppCard, CircularProgressBar


class HomeView(QWidget):
    # Signal definitions
    start_app_clicked = pyqtSignal()
    stop_app_clicked = pyqtSignal()
    start_pomodoro_clicked = pyqtSignal()
    end_pomodoro_clicked = pyqtSignal()
    request_initial_data = pyqtSignal()
    request_updated_daily_report = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
                QFrame {
                    background-color: #20223e;
                    border-radius: 10px;
                    text-align: center;
                }
                """)
        self.setup_ui()
        self.staged_data = True

    def setup_ui(self):
        home_layout = QGridLayout(self)
        home_layout.setContentsMargins(20, 20, 20, 20)
        home_layout.setHorizontalSpacing(75)
        home_layout.setVerticalSpacing(25)

        app_control_frame = self._create_app_control_section()
        session_frame = self._create_workday_section()
        pomodoro_frame = self._create_pomodoro_section()
        active_apps_frame = self._create_active_apps_section()

        for frame in [app_control_frame, session_frame, pomodoro_frame, active_apps_frame]:
            frame.setContentsMargins(25, 0, 25, 10)
            frame.resize(350, 300)

        home_layout.addWidget(app_control_frame, 0, 0)
        home_layout.addWidget(session_frame, 0, 1)
        home_layout.addWidget(pomodoro_frame, 1, 0)
        home_layout.addWidget(active_apps_frame, 1, 1)

    def update_application_status(self, is_tracking: bool):
        # app control section
        self.start_button.setVisible(not is_tracking)
        self.stop_button.setVisible(is_tracking)
        self.pomodoro_start_button.setEnabled(is_tracking and int(self.pomodoros_remaining.text()) > 0)
        self.status_indicator.setStyleSheet(
            "color: #4ade80; font-size: 24px;" if is_tracking else
            "color: #ef4444; font-size: 24px;"
        )
        self.status_text.setText(
            "Application Running" if is_tracking else "Application Stopped"
        )
        self.start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.request_updated_daily_report.emit() if not is_tracking else None

    def showEvent(self, event):
        super().showEvent(event)
        self.start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_button.setCursor(Qt.CursorShape.PointingHandCursor)

    def update_productive_time(self, time: int, current_app_time: int):
        hours, minutes = divmod(time // 60, 60)
        self.prod_time_value.setText(f"{hours}:{minutes:02d}")

        if current_app_time:
            self.update_recent_application_time(current_app_time)

    def update_non_productive_time(self, time: int, current_app_time: int):
        hours, minutes = divmod(time // 60, 60)
        self.nonprod_time_value.setText(f"{hours}:{minutes:02d}")

        if current_app_time:
            self.update_recent_application_time(current_app_time)

    def update_pomodoro_status(self, time: int, pomodoros_remaining: int, is_active=False):
        if is_active:
            self.pomodoros_remaining.setText(str(pomodoros_remaining))
            self.pomodoro_timer.setValue(time)
            self.pomodoro_start_button.setVisible(False)
            self.pomodoro_end_button.setVisible(True)
            self.pomodoro_start_button.setEnabled(False) if pomodoros_remaining == 0 else None
        else:
            self.pomodoro_timer.setValue(self.pomodoro_timer.max_value)
            self.pomodoro_start_button.setVisible(True)
            self.pomodoro_end_button.setVisible(False)

    def update_pomodoro_time(self, time: int):
        self.pomodoro_timer.setValue(time)

    def update_pomodoros_remaining(self, pomodoros_remaining: int):
        self.pomodoros_remaining.setText(str(pomodoros_remaining))
        self.pomodoro_start_button.setEnabled(False) if pomodoros_remaining == 0 else None

    def update_recent_applications(self, new_app: ApplicationView):
        if self.active_apps_layout.count() > 4:  # index 0 + 4 app cards
            last_item = self.active_apps_layout.takeAt(4)
            if last_item.widget():
                last_item.widget().deleteLater()

        app_card = AppCard(new_app.name, new_app.elapsed_time)

        # Set color based on productivity
        if new_app.is_productive:
            app_card.setStyleSheet(app_card.styleSheet() + "#appCard { border-left: 5px solid #4ade80; }")
        else:
            app_card.setStyleSheet(app_card.styleSheet() + "#appCard { border-left: 5px solid #ef4444; }")

        self.active_apps_layout.insertWidget(1, app_card)

        self.active_apps_layout.addStretch()

    def update_recent_application_time(self, time=None):
        if self.active_apps_layout.count() > 1:
            item = self.active_apps_layout.itemAt(1)
            if item and item.widget():
                app_card = item.widget()
                app_card.update_time(time)

    def _on_start_app_clicked(self):
        if self.staged_data:
            while self.active_apps_layout.count() > 1:
                last_item = self.active_apps_layout.takeAt(1)
                if last_item.widget():
                    last_item.widget().deleteLater()
            self.staged_data = False
            self.active_apps_layout.addStretch()

        self.start_app_clicked.emit()

    def _on_stop_app_clicked(self):
        self.stop_app_clicked.emit()

    def _on_start_pomodoro_clicked(self):
        self.start_pomodoro_clicked.emit()

    def _on_end_pomodoro_clicked(self):
        self.end_pomodoro_clicked.emit()

    def _create_app_control_section(self):
        # Frame
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Metadata
        title = QLabel("Application Control")
        title.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        # Buttons
        buttons_layout = QHBoxLayout()

        self.start_button = QPushButton("▶ Start")
        self.start_button.setFixedHeight(50)
        self.start_button.clicked.connect(self._on_start_app_clicked)

        self.stop_button = QPushButton("■ Stop")
        self.stop_button.setObjectName("cancelButton")
        self.stop_button.setFixedHeight(50)
        self.stop_button.clicked.connect(self._on_stop_app_clicked)
        self.stop_button.setVisible(False)

        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        layout.addLayout(buttons_layout)

        # Create status indicator
        status_frame = QFrame()
        status_frame.setStyleSheet("background-color: #2d3142;")
        status_layout = QHBoxLayout(status_frame)

        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #ef4444; font-size: 24px;")

        self.status_text = QLabel("Application Stopped")
        self.status_text.setStyleSheet("font-size: 16px;")
        self.status_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        status_layout.addWidget(self.status_indicator)
        status_layout.addStretch()
        status_layout.addWidget(self.status_text)
        status_layout.addStretch()

        layout.addWidget(status_frame)
        layout.addStretch()

        return frame

    def _create_workday_section(self):
        workday_frame = QFrame()
        workday_layout = QVBoxLayout(workday_frame)
        workday_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        workday_title = QLabel("Current Workday")
        workday_title.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        workday_title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        workday_layout.addWidget(workday_title)

        # Time counters
        time_layout = QHBoxLayout()
        time_layout.setSpacing(20)

        # Productive time
        prod_time_frame = QFrame()
        prod_time_frame.setObjectName("prodTimeFrame")
        prod_time_frame.setStyleSheet("""
            #prodTimeFrame {
                border-radius: 8px;
                background-color: #2d3142;
            }
            #prodTimeFrame QLabel {
                background-color: transparent;
            }
        """)

        prod_time_layout = QVBoxLayout(prod_time_frame)
        prod_time_label = QLabel("Productive Time")
        prod_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        prod_time_label.setStyleSheet("font-size: 14px; font-weight: bold;")

        self.prod_time_value = QLabel("0:45")
        self.prod_time_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prod_time_value.setStyleSheet("font-size: 48px; color: #4ade80; font-weight: bold;")

        prod_time_unit = QLabel("hours")
        prod_time_unit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        prod_time_unit.setStyleSheet("font-size: 14px;")

        prod_time_layout.addWidget(prod_time_label)
        prod_time_layout.addWidget(self.prod_time_value)
        prod_time_layout.addWidget(prod_time_unit)

        # Non-productive time
        non_prod_time_frame = QFrame()
        non_prod_time_frame.setObjectName("nonProdTimeFrame")
        non_prod_time_frame.setStyleSheet("""
                    #nonProdTimeFrame {
                        border-radius: 8px;
                        background-color: #2d3142;
                    }
                    #nonProdTimeFrame QLabel {
                        background-color: transparent;
                    }
                """)

        nonprod_time_layout = QVBoxLayout(non_prod_time_frame)
        nonprod_time_label = QLabel("Non-Productive Time")
        nonprod_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nonprod_time_label.setStyleSheet("font-size: 14px; font-weight: bold;")

        self.nonprod_time_value = QLabel("0:25")
        self.nonprod_time_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nonprod_time_value.setStyleSheet("font-size: 48px; color: #ef4444; font-weight: bold;")

        nonprod_time_unit = QLabel("hours")
        nonprod_time_unit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nonprod_time_unit.setStyleSheet("font-size: 14px;")

        nonprod_time_layout.addWidget(nonprod_time_label)
        nonprod_time_layout.addWidget(self.nonprod_time_value)
        nonprod_time_layout.addWidget(nonprod_time_unit)

        prod_time_frame.setMinimumWidth(175)
        non_prod_time_frame.setMinimumWidth(175)
        time_layout.addWidget(prod_time_frame, 1)
        time_layout.addWidget(non_prod_time_frame, 1)

        workday_layout.addLayout(time_layout)
        workday_layout.addStretch()

        return workday_frame

    def _create_pomodoro_section(self):
        pomodoro_frame = QFrame()
        pomodoro_layout = QVBoxLayout(pomodoro_frame)
        pomodoro_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pomodoro_layout.setSpacing(25)

        pomodoro_layout.addStretch()

        pomodoro_title = QLabel("Pomodoro Timer")
        pomodoro_title.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        pomodoro_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        pomodoro_layout.addWidget(pomodoro_title)

        # Timer display
        timer_layout = QHBoxLayout()

        # Circular progress bar
        self.pomodoro_timer = CircularProgressBar()
        self.pomodoro_timer.setMinimumSize(175, 175)
        self.pomodoro_timer.setText("", ":00")

        timer_layout.addWidget(self.pomodoro_timer, 3, Qt.AlignmentFlag.AlignCenter)

        # Pomodoros remaining
        pomodoros_frame = QFrame()
        pomodoros_frame.setStyleSheet("background-color: #2d3142;")
        pomodoros_layout = QVBoxLayout(pomodoros_frame)

        pomodoros_header = QLabel("Pomodoros")
        pomodoros_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pomodoros_header.setStyleSheet("font-size: 20px;")

        self.pomodoros_remaining = QLabel("4")
        self.pomodoros_remaining.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pomodoros_remaining.setStyleSheet("font-size: 48px; font-weight: bold;")

        pomodoros_label = QLabel("remaining")
        pomodoros_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pomodoros_label.setStyleSheet("font-size: 14px;")

        pomodoros_layout.addWidget(pomodoros_header)
        pomodoros_layout.addWidget(self.pomodoros_remaining)
        pomodoros_layout.addWidget(pomodoros_label)

        timer_layout.addWidget(pomodoros_frame, 2, Qt.AlignmentFlag.AlignCenter)

        pomodoro_layout.addLayout(timer_layout)

        # Timer controls
        timer_buttons_layout = QHBoxLayout()

        self.pomodoro_start_button = QPushButton("▶ Pomodoro")
        self.pomodoro_start_button.setFixedHeight(50)
        self.pomodoro_start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pomodoro_start_button.setEnabled(False)
        self.pomodoro_start_button.clicked.connect(self._on_start_pomodoro_clicked)

        self.pomodoro_end_button = QPushButton("■ End")
        self.pomodoro_end_button.setObjectName("cancelButton")
        self.pomodoro_end_button.setFixedHeight(50)
        self.pomodoro_end_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pomodoro_end_button.setVisible(False)
        self.pomodoro_end_button.clicked.connect(self._on_end_pomodoro_clicked)

        timer_buttons_layout.addWidget(self.pomodoro_start_button)
        timer_buttons_layout.addWidget(self.pomodoro_end_button)

        pomodoro_layout.addLayout(timer_buttons_layout)
        pomodoro_layout.addStretch()

        return pomodoro_frame

    def _create_active_apps_section(self):
        active_apps_frame = QFrame()
        self.active_apps_layout = QVBoxLayout(active_apps_frame)
        self.active_apps_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        active_apps_title = QLabel("Recent Applications")
        active_apps_title.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        active_apps_title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        self.active_apps_layout.addWidget(active_apps_title)

        self.update_recent_applications(ApplicationView(name="VS Code", is_productive=True, elapsed_time=25))
        self.update_recent_applications(ApplicationView(name="Terminal", is_productive=True, elapsed_time=15))
        self.update_recent_applications(ApplicationView(name="Slack", is_productive=False, elapsed_time=10))
        self.update_recent_applications(ApplicationView(name="Twitter", is_productive=True, elapsed_time=55))

        self.active_apps_layout.addStretch()

        return active_apps_frame
