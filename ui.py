from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QBrush, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsPixmapItem,
    QGraphicsPolygonItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from simulator import ValveSimulator
from hydraulics import ValveState


ASSET_DIR = Path(__file__).resolve().parent / "assets"

MANIFOLD_ASSETS = {
    ("open", "open"): "BlockAndBleed-open-open.png",
    ("open", "close"): "BlockAndBleed-open-close.png",
    ("close", "open"): "BlockAndBleed-close-open.png",
    ("close", "close"): "BlockAndBleed-close-close.png",
}


class ClickableRectItem(QGraphicsRectItem):
    def __init__(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        callback,
        pen: QPen,
        brush: QBrush,
    ) -> None:
        super().__init__(x, y, w, h)
        self.callback = callback
        self.setPen(pen)
        self.setBrush(brush)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            event.accept()
            self.callback()
            return
        event.ignore()

    def hoverEnterEvent(self, event) -> None:
        self.setOpacity(0.8)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self.setOpacity(1.0)
        super().hoverLeaveEvent(event)


class ClickablePixmapItem(QGraphicsPixmapItem):
    def __init__(self, pixmap: QPixmap, callback) -> None:
        super().__init__(pixmap)
        self.callback = callback
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            event.accept()
            self.callback()
            return
        event.ignore()

    def hoverEnterEvent(self, event) -> None:
        self.setOpacity(0.85)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self.setOpacity(1.0)
        super().hoverLeaveEvent(event)


class GraphicsView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene) -> None:
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setBackgroundBrush(QColor("white"))
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)


class ValveSimulatorUI(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Hydraulic Valve Simulator")
        self.resize(1300, 900)

        self.sim = ValveSimulator()

        self.status_label = QLabel("Ready")
        self.pixmap_cache: dict[tuple[str, int, int], QPixmap] = {}

        self.common_close_returns = 0
        self.open_returns: list[int] = [0 for _ in self.sim.valves]

        self.scene = QGraphicsScene(self)
        self.view = GraphicsView(self.scene)

        self._build_ui()
        self.redraw()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(10)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        add_valve_btn = QPushButton("Add Valve")
        add_valve_btn.clicked.connect(self.add_valve)

        top_bar.addWidget(add_valve_btn)
        top_bar.addWidget(self.status_label)
        top_bar.addStretch()

        root_layout.addLayout(top_bar)
        root_layout.addWidget(self.view)

    def add_valve(self) -> None:
        self.sim.add_valve()
        self.open_returns.append(0)
        self.status_label.setText(f"FCV-{len(self.sim.valves)} added")
        self.redraw()

    def actuate(self) -> None:
        results = self.sim.actuate()

        moved: list[str] = []
        for i, result in enumerate(results, start=1):
            if result.movement:
                moved.append(f"FCV-{i}")

            if result.return_line is self.sim.common_close_line:
                self.common_close_returns = result.fluid_returns or 0

            for j, line in enumerate(self.sim.lines):
                if result.return_line is line:
                    self.open_returns[j] = result.fluid_returns or 0
                    break

        self.status_label.setText(
            "Moved: " + ", ".join(moved) if moved else "No valve movement"
        )
        self.redraw()

    def redraw(self) -> None:
        self.scene.clear()

        top_y = 110
        left_x = 70
        trunk_x = 250
        manifold_x = 300
        fcv_x = 1080
        row_h = 170

        scene_height = max(900, top_y + row_h * (len(self.sim.valves) + 2))
        self.scene.setSceneRect(0, 0, 1400, scene_height)

        self._add_text(40, 35, "Hydraulic Valve Simulator", size=16, bold=True)

        pump_pixmap = self._get_pump_pixmap(width=110, height=70)
        pump_x = left_x
        pump_y = top_y - 35

        self._add_text(pump_x - 10, pump_y - 18, "Pump / Supply", size=10)

        pump_item = ClickablePixmapItem(pump_pixmap, self.actuate)
        pump_item.setPos(pump_x, pump_y)
        self.scene.addItem(pump_item)

        self.scene.addRect(
            QRectF(pump_x, pump_y, 110, 70),
            QPen(QColor("#1f77b4"), 2, Qt.PenStyle.DashLine),
        )
        self._add_text(
            pump_x + 8,
            pump_y + 84,
            "Click pump to actuate",
            size=10,
            color="#1f77b4",
        )

        self.scene.addLine(
            pump_x + 110,
            top_y,
            manifold_x,
            top_y,
            QPen(Qt.GlobalColor.black, 2),
        )

        last_y = top_y + row_h * max(1, len(self.sim.valves))
        self.scene.addLine(
            trunk_x,
            top_y,
            trunk_x,
            last_y,
            QPen(Qt.GlobalColor.black, 2),
        )

        self._draw_row(
            y=top_y,
            title="Common Close Line",
            manifold=self.sim.common_close_manifold,
            line_state=self.sim.common_close_line.state.value,
            returns=self.common_close_returns,
            manifold_x=manifold_x,
            fcv_x=None,
            index=None,
            common=True,
        )

        for i, valve in enumerate(self.sim.valves):
            y = top_y + row_h * (i + 1)
            self.scene.addLine(
                trunk_x,
                y,
                manifold_x,
                y,
                QPen(Qt.GlobalColor.black, 2),
            )

            self._draw_row(
                y=y,
                title=f"Open Line {i + 1}",
                manifold=self.sim.manifolds[i],
                line_state=self.sim.lines[i].state.value,
                returns=self.open_returns[i],
                manifold_x=manifold_x,
                fcv_x=fcv_x,
                index=i,
                common=False,
            )

            self._draw_fcv(fcv_x, y, f"FCV-{i + 1}", valve.choke.value)

    def _draw_row(
        self,
        y: int,
        title: str,
        manifold,
        line_state: str,
        returns: int,
        manifold_x: int,
        fcv_x: int | None,
        index: int | None,
        common: bool,
    ) -> None:
        pixmap = self._get_manifold_pixmap(manifold, width=240, height=120)
        img_w = pixmap.width()

        item = QGraphicsPixmapItem(pixmap)
        item.setPos(manifold_x, y - 10)
        self.scene.addItem(item)

        self._add_text(manifold_x + img_w + 10, y + 5, title, size=12)
        self._add_text(manifold_x + img_w + 10, y + 30, f"Line: {line_state}", size=11)
        self._add_text(manifold_x + img_w + 10, y + 55, f"Returns: {returns}", size=11)

        line_y = y + 45
        line_start = manifold_x + img_w - 5
        line_end = (fcv_x - 20) if fcv_x is not None else 1030
        self._draw_arrow(line_start, line_y, line_end, line_y)

        block_box = (manifold_x + 58, y + 5, 97, 37)
        bleed_box = (manifold_x + 58, y + 58, 97, 38)

        green_pen = QPen(QColor("#2ca02c"), 2)
        green_brush = QBrush(QColor(204, 255, 204, 120))

        red_pen = QPen(QColor("#d62728"), 2)
        red_brush = QBrush(QColor(255, 214, 214, 120))

        if common:
            block_item = ClickableRectItem(
                block_box[0],
                block_box[1],
                block_box[2],
                block_box[3],
                lambda: self.toggle_common("block"),
                green_pen,
                green_brush,
            )
            bleed_item = ClickableRectItem(
                bleed_box[0],
                bleed_box[1],
                bleed_box[2],
                bleed_box[3],
                lambda: self.toggle_common("bleed"),
                red_pen,
                red_brush,
            )
        else:
            assert index is not None

            block_item = ClickableRectItem(
                block_box[0],
                block_box[1],
                block_box[2],
                block_box[3],
                lambda i=index: self.toggle_open(i, "block"),
                green_pen,
                green_brush,
            )
            bleed_item = ClickableRectItem(
                bleed_box[0],
                bleed_box[1],
                bleed_box[2],
                bleed_box[3],
                lambda i=index: self.toggle_open(i, "bleed"),
                red_pen,
                red_brush,
            )

        self.scene.addItem(block_item)
        self.scene.addItem(bleed_item)

        self._add_text(
            block_box[0] + 20,
            block_box[1] - 16,
            "BLOCK",
            size=9,
            bold=True,
            color="#2ca02c",
        )
        self._add_text(
            bleed_box[0] + 20,
            bleed_box[1] - 16,
            "BLEED",
            size=9,
            bold=True,
            color="#d62728",
        )

    def _draw_fcv(self, x: int, y: int, label: str, position: str) -> None:
        pen = QPen(Qt.GlobalColor.black, 1)

        self.scene.addRect(QRectF(x, y + 10, 35, 100), pen)
        self.scene.addRect(QRectF(x + 8, y + 20, 12, 22), pen)
        self.scene.addRect(QRectF(x + 8, y + 80, 12, 22), pen)

        self._add_text(x + 45, y + 25, label, size=11)

        # White backing box for the position text to fully cover previous text.
        self.scene.addRect(
            QRectF(x + 42, y + 46, 170, 24),
            QPen(Qt.PenStyle.NoPen),
            QBrush(QColor("white")),
        )
        self._add_text(x + 45, y + 50, f"Pos: {position}", size=10)

    def toggle_common(self, part: str) -> None:
        manifold = self.sim.common_close_manifold
        if part == "block":
            manifold.block = self._toggle(manifold.block)
        else:
            manifold.bleed = self._toggle(manifold.bleed)
        self.redraw()

    def toggle_open(self, index: int, part: str) -> None:
        manifold = self.sim.manifolds[index]
        if part == "block":
            manifold.block = self._toggle(manifold.block)
        else:
            manifold.bleed = self._toggle(manifold.bleed)
        self.redraw()

    @staticmethod
    def _toggle(state: ValveState) -> ValveState:
        return ValveState.CLOSED if state == ValveState.OPEN else ValveState.OPEN

    def _get_pump_pixmap(self, width: int = 110, height: int = 70) -> QPixmap:
        key = ("__pump__", width, height)
        if key not in self.pixmap_cache:
            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)

            painter.drawEllipse(8, 12, 44, 44)

            triangle = QPolygonF(
                [
                    QPointF(40, 34),
                    QPointF(28, 24),
                    QPointF(28, 44),
                ]
            )
            painter.setBrush(QBrush(Qt.GlobalColor.black))
            painter.drawPolygon(triangle)

            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(Qt.GlobalColor.black, 4))
            painter.drawLine(52, 34, width - 8, 34)

            painter.end()
            self.pixmap_cache[key] = pixmap

        return self.pixmap_cache[key]

    def _get_manifold_pixmap(self, manifold, width: int = 240, height: int = 120) -> QPixmap:
        block = "open" if manifold.block == ValveState.OPEN else "close"
        bleed = "open" if manifold.bleed == ValveState.OPEN else "close"
        filename = MANIFOLD_ASSETS[(block, bleed)]
        path = ASSET_DIR / filename

        key = (str(path), width, height)
        if key not in self.pixmap_cache:
            pixmap = QPixmap(str(path))
            if pixmap.isNull():
                raise FileNotFoundError(f"Could not load manifold image: {path}")
            self.pixmap_cache[key] = pixmap.scaled(
                width,
                height,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        return self.pixmap_cache[key]

    def _add_text(
        self,
        x: float,
        y: float,
        text: str,
        size: int = 10,
        bold: bool = False,
        color: str = "black",
    ) -> QGraphicsSimpleTextItem:
        item = QGraphicsSimpleTextItem(text)
        font = item.font()
        font.setPointSize(size)
        font.setBold(bold)
        item.setFont(font)
        item.setBrush(QBrush(QColor(color)))
        item.setPos(x, y)
        self.scene.addItem(item)
        return item

    def _draw_arrow(self, x1: float, y1: float, x2: float, y2: float) -> None:
        pen = QPen(Qt.GlobalColor.black, 2)
        self.scene.addLine(x1, y1, x2, y2, pen)

        arrow_size = 8
        arrow = QPolygonF(
            [
                QPointF(x2, y2),
                QPointF(x2 - arrow_size, y2 - 4),
                QPointF(x2 - arrow_size, y2 + 4),
            ]
        )
        arrow_item = QGraphicsPolygonItem(arrow)
        arrow_item.setPen(pen)
        arrow_item.setBrush(QBrush(Qt.GlobalColor.black))
        self.scene.addItem(arrow_item)


def main() -> None:
    app = QApplication([])
    window = ValveSimulatorUI()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
