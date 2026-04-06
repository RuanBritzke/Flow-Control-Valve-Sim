from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtSvgWidgets import QSvgWidget


class ManifoldWidget(QWidget):
    def __init__(self, svg_path: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.svg = QSvgWidget(str(svg_path))
        self.svg.setFixedSize(260, 140)
        self.svg.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.svg, alignment=Qt.AlignmentFlag.AlignCenter)