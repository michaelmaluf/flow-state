import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class PieChart(FigureCanvas):
    def __init__(self, parent=None, width=5, height=5, dpi=100):
        self.fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)

        # Set the background color to match the app's dark theme
        self.fig.patch.set_facecolor('#1e2130')
        self.ax.set_facecolor('#1e2130')

    def update_chart(self, sizes, labels, colors):
        self.ax.clear()
        self.ax.pie(sizes, labels=labels, colors=colors, autopct='%1.0f%%',
                    startangle=90, textprops={'color': 'white', 'fontsize': 12, 'fontweight': 'bold'})
        self.ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        self.draw()