from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QColor, QPainter, QPen, QFont
from PyQt6.QtWidgets import QWidget


class CircularProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 600
        self.max_value = 600
        self.progress_width = 10
        self.progress_color = QColor(65, 105, 225)
        self.bg_color = QColor(40, 44, 52, 100)
        self.text_color = QColor(255, 255, 255)
        self.prefix = ""
        self.suffix = ""
        self.text_size = 30

    def setValue(self, value):
        # self.pomodoro_timer.setText("", ":00")
        self.prefix, self.suffix = divmod(value, 60)
        self.value = value
        self.update()

    def setMaxValue(self, max_value):
        self.max_value = max_value
        self.update()

    def setProgressWidth(self, width):
        self.progress_width = width
        self.update()

    def setProgressColor(self, color):
        self.progress_color = color
        self.update()

    def setBackgroundColor(self, color):
        self.bg_color = color
        self.update()

    def setText(self, prefix, suffix):
        self.prefix = prefix
        self.suffix = suffix
        self.update()

    def setTextSize(self, size):
        self.text_size = size
        self.update()

    def paintEvent(self, event):
        width = self.width()
        height = self.height()
        margin = self.progress_width / 2
        value = self.value * 360 / self.max_value

        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(width / 2, height / 2)
        painter.rotate(270)

        # Background
        painter.setPen(QPen(self.bg_color, self.progress_width, Qt.PenStyle.SolidLine))
        painter.drawArc(
            int(-width / 2 + margin),
            int(-height / 2 + margin),
            int(width - self.progress_width),
            int(height - self.progress_width),
            0,
            360 * 16
        )

        # Progress
        painter.setPen(QPen(self.progress_color, self.progress_width, Qt.PenStyle.SolidLine))
        painter.drawArc(
            int(-width / 2 + margin),
            int(-height / 2 + margin),
            int(width - self.progress_width),
            int(height - self.progress_width),
            0,
            int(value * 16)
        )

        # Text
        painter.rotate(90)
        painter.setPen(self.text_color)
        font = QFont("Arial", self.text_size, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(
            QRect(
                int(-width / 2),
                int(-height / 2),
                int(width),
                int(height)
            ),
            Qt.AlignmentFlag.AlignCenter,
            f"{self.value//60}:{self.value%60:02d}"
        )

        painter.end()