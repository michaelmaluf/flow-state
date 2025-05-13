import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initTray()

    def initUI(self):
        self.setWindowTitle('My App')
        self.setGeometry(100, 100, 800, 600)
        self.show()

    def initTray(self):
        # Create the tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('images/icon.jpg'))

        # Create the tray menu
        tray_menu = QMenu()

        show_action = QAction('Show/Hide', self)
        show_action.triggered.connect(self.toggleWindow)
        tray_menu.addAction(show_action)

        quit_action = QAction('Quit', self)
        quit_action.triggered.connect(QApplication.instance().quit)  # Changed app.quit to QApplication.instance().quit
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.trayActivated)
        self.tray_icon.show()

    def toggleWindow(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            # Updated window state handling for PyQt6
            self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
            self.activateWindow()

    def trayActivated(self, reason):
        # Updated enum reference for PyQt6
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggleWindow()

    def closeEvent(self, event):
        # Override close event to hide instead of quit
        event.ignore()
        self.hide()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    main_app = MainApp()
    sys.exit(app.exec())