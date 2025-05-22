from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QFrame)


class AppCard(QFrame):
    def __init__(self, app_name, time_spent, percentage=None, parent=None):
        super().__init__(parent)
        self.setObjectName("appCard")
        self.setStyleSheet("""
            #appCard {
                background-color: #2d3142;
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }
        """)

        layout = QHBoxLayout(self)

        app_label = QLabel(app_name)
        app_label.setStyleSheet("color: white; font-size: 16px;")

        if time_spent == 0:
            time_text = "~"
        else:
            minutes, seconds = divmod(time_spent, 60)
            time_text = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"

        if percentage:
            time_text += f" ({percentage})"

        time_label = QLabel(time_text)
        time_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        layout.addWidget(app_label)
        layout.addStretch()
        layout.addWidget(time_label)

        self.setLayout(layout)