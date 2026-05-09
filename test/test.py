import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QFont, QColor
from PyQt6.QtCore import Qt
import win32gui
import win32con


class Overlay(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # fullscreen overlay
        self.setGeometry(0, 0, 1920, 1080)

        self.show()

        # make window click-through
        hwnd = int(self.winId())

        style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(
            hwnd,
            win32con.GWL_EXSTYLE,
            style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
        )

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setFont(QFont("Arial", 40))
        painter.setPen(QColor(255, 0, 0))

        painter.drawText(500, 300, "OVERLAY TEST")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    overlay = Overlay()

    sys.exit(app.exec())