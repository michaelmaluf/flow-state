from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QColor, QFont, QPen
from PyQt6.QtWidgets import QWidget


class PieChart(QWidget):
    def __init__(self, productive_percent=65, parent=None):
        super().__init__(parent)
        self.productive_percent = productive_percent
        self.non_productive_percent = 100 - productive_percent
        self.setMinimumSize(225, 225)

    def set_data(self, productive_percent):
        """Update the chart data"""
        self.productive_percent = productive_percent
        self.non_productive_percent = 100 - productive_percent
        self.update()  # Trigger a repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Get widget dimensions
        width = self.width()
        height = self.height()
        side = min(width, height)

        # Calculate chart rectangle (leave margin for text)
        margin = 5
        chart_size = side - (margin * 2)
        chart_rect = QRect(
            (width - chart_size) // 2,
            (height - chart_size) // 2,
            chart_size,
            chart_size
        )

        # Colors
        productive_color = QColor("#4ade80")
        non_productive_color = QColor("#ef4444")

        # Calculate angles (Qt uses 16ths of a degree)
        productive_angle = int(self.productive_percent * 3.6 * 16)
        non_productive_angle = int(self.non_productive_percent * 3.6 * 16)

        # Draw productive slice (start from top, 90 degrees = 1440 sixteenths)
        painter.setBrush(productive_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPie(chart_rect, 1440, productive_angle)

        # Draw non-productive slice
        painter.setBrush(non_productive_color)
        painter.drawPie(chart_rect, 1440 + productive_angle, non_productive_angle)

        painter.setPen(QPen(QColor("white")))
        font = QFont("Arial", 14, QFont.Weight.Bold)
        painter.setFont(font)

        # center_x = width // 2
        # center_y = height // 2
        # radius = chart_size // 3
        #
        # prod_angle_mid = math.radians(90 - (self.productive_percent * 3.6 / 2))
        # prod_x = center_x + radius * math.cos(prod_angle_mid)
        # prod_y = center_y - radius * math.sin(prod_angle_mid)

        # Draw productive text
        # prod_text = f"{self.productive_percent}% Prod."
        # painter.drawText(int(prod_x - 150), int(prod_y), prod_text)

        # non_prod_angle_start = 90 - self.productive_percent * 3.6
        # non_prod_angle_mid = math.radians(non_prod_angle_start - (self.non_productive_percent * 3.6 / 2))
        # non_prod_x = center_x + radius * math.cos(non_prod_angle_mid)
        # non_prod_y = center_y - radius * math.sin(non_prod_angle_mid)

        # Draw non-productive text
        # non_prod_text = f"{self.non_productive_percent}% Non-Prod."
        # painter.drawText(int(non_prod_x + 100), int(non_prod_y), non_prod_text)