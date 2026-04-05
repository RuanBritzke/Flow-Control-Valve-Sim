from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QWidget
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

class PumpWidget(QLabel):
    def __init__(self, pixmap, callback, parent=None):
        super().__init__(parent)
        self.callback = callback

        self.setPixmap(pixmap)
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setMinimumSize(200, 200)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.callback()
            event.accept()
            return
        event.ignore()