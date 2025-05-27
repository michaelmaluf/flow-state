from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect)


class AppCard(QFrame):
    def __init__(self, app_name, time_spent, percentage=None, parent=None):
        super().__init__(parent)
        self.setObjectName("appCard")
        self.setStyleSheet("""
            #appCard {
                background-color: #2d3142;
                border-radius: 8px;
                padding: 3px;
                margin: 2px;
            }
            #appCard QLabel {
                background-color: transparent;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)

        app_label = QLabel(app_name)
        app_label.setStyleSheet("color: white; font-size: 16px;")

        if time_spent == 0:
            time_text = "~"
        else:
            minutes, seconds = divmod(time_spent, 60)
            time_text = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"

        if percentage is not None:
            hours, seconds = divmod(time_spent, 3600)
            time_text = f"{hours}h {seconds//60}m" if hours else f"{seconds//60}m"
            time_text += f" ({percentage}%)"

        time_label = QLabel(time_text)
        time_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        layout.addWidget(app_label)
        layout.addStretch()
        layout.addWidget(time_label)

        # self.setLayout(layout)