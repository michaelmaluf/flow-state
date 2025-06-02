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
            time_text = "0s" if percentage is not None else "~"
        elif time_spent >= 3600:
            h, rem = divmod(time_spent, 3600)
            m = rem // 60
            time_text = f"{h}h {m}m" if m else f"{h}h"
        elif percentage is not None:
            m = round(time_spent / 60)
            time_text = f"{m}m" if m else f"{time_spent}s"
        else:
            m, s = divmod(time_spent, 60)
            time_text = f"{m}m {s}s" if m and s else f"{m}m" if m else f"{s}s"

        if percentage is not None:
            time_text += f" ({percentage}%)"

        self.time_label = QLabel(time_text)
        self.time_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        layout.addWidget(app_label)
        layout.addStretch()
        layout.addWidget(self.time_label)

        # self.setLayout(layout)

    def update_time(self, time: int):
        minutes, seconds = divmod(time, 60)
        time_text = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
        self.time_label.setText(time_text)
        self.update()
