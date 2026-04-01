from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QBrush, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtSvg import QSvgRenderer
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
    ("open", "open"): "BlockAndBleed-open-open.svg",
    ("open", "close"): "BlockAndBleed-open-close.svg",
    ("close", "open"): "BlockAndBleed-close-open.svg",
    ("close", "close"): "BlockAndBleed-close-close.svg",
}

VALVE_ASSETS = {
    "Fully Closed": "TRFC_FC.svg",
    "Fully Open": "TRFC_FO.svg",
    "1": "TRFC_P1.svg",
    "2": "TRFC_P2.svg",
    "3": "TRFC_P3.svg",
    "4": "TRFC_P4.svg",
    "5": "TRFC_P5.svg",
    "6": "TRFC_P6.svg",
    "7": "TRFC_P7.svg",
    "8": "TRFC_P8.svg",
}


class ClickableRectItem(QGraphicsRectItem):
    def __init__(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        callback,
        pen: QPen | None = None,
        brush: QBrush | None = None,
    ) -> None:
        super().__init__(x, y, w, h)
        self.callback = callback
        self.setPen(pen if pen is not None else QPen(Qt.PenStyle.NoPen))
        self.setBrush(brush if brush is not None else QBrush(Qt.BrushStyle.NoBrush))
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
        self.setStyleSheet("background: white;")


class ValveSimulatorUI(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Hydraulic Valve Simulator")
        self.resize(1500, 900)

        self.sim = ValveSimulator()

        self.status_label = QLabel("Ready")
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QBrush(QColor("white")))
        self.view = GraphicsView(self.scene)

        self.pixmap_cache: dict[tuple[str, int, int], QPixmap] = {}

        self.common_close_returns = 0
        self.open_returns: list[int] = [0 for _ in self.sim.valves]
        self.last_move_message = "No valve movement"

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

        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_simulator)

        top_bar.addWidget(add_valve_btn)
        top_bar.addWidget(reset_btn)
        top_bar.addWidget(self.status_label)
        top_bar.addStretch()

        root_layout.addLayout(top_bar)
        root_layout.addWidget(self.view)

    def add_valve(self) -> None:
        self.sim.add_valve()
        self.open_returns.append(0)
        self.status_label.setText(f"FCV-{len(self.sim.valves)} added")
        self.last_move_message = "No valve movement"
        self.redraw()

    def reset_simulator(self) -> None:
        self.sim.reset()
        self.common_close_returns = 0
        self.open_returns = [0 for _ in self.sim.valves]
        self.last_move_message = "No valve movement"
        self.status_label.setText("Simulator reset")
        self.redraw()

    def actuate(self) -> None:
        results = self.sim.actuate()

        moved: list[str] = []
        self.common_close_returns = 0
        self.open_returns = [0 for _ in self.sim.valves]

        for i, result in enumerate(results, start=1):
            if result.movement:
                moved.append(f"FCV-{i}")

            if result.return_line is self.sim.common_close_line:
                self.common_close_returns = result.fluid_returns or 0

            for j, line in enumerate(self.sim.lines):
                if result.return_line is line:
                    self.open_returns[j] = result.fluid_returns or 0
                    break

        self.last_move_message = (
            "Moved: " + ", ".join(moved) if moved else "No valve movement"
        )
        self.status_label.setText(self.last_move_message)
        self.redraw()

    def redraw(self) -> None:
        self.scene.clear()
        self.scene.setBackgroundBrush(QBrush(QColor("white")))

        margin_x = 40
        header_y = 30
        top_y = 90
        row_gap = 30

        col1_x = margin_x
        col2_x = 260
        col3_x = 650
        col4_x = 900

        manifold_w = 260
        manifold_h = 140
        valve_w = 180
        valve_h = 160

        row_height = valve_h + row_gap

        scene_width = 1350
        scene_height = max(900, top_y + row_height * max(2, len(self.sim.valves) + 1))
        self.scene.setSceneRect(0, 0, scene_width, scene_height)

        self._add_text(40, 20, "Hydraulic Valve Simulator", size=16, bold=True)

        self._add_text(col1_x, header_y, "Pump", size=11, bold=True)
        self._add_text(col2_x, header_y, "Block and Bleed Manifolds", size=11, bold=True)
        self._add_text(col3_x, header_y, "Valves", size=11, bold=True)
        self._add_text(col4_x, header_y, "Valve Information", size=11, bold=True)

        message_row_y = top_y
        common_row_y = top_y + row_height

        # Column 1: pump only
        pump_pixmap = self._get_pump_pixmap(120, 80)
        pump_item = ClickablePixmapItem(pump_pixmap, self.actuate)
        pump_item.setPos(col1_x + 20, common_row_y + 10)
        self.scene.addItem(pump_item)

        self.scene.addRect(
            QRectF(col1_x + 15, common_row_y + 5, 130, 90),
            QPen(QColor("#1f77b4"), 2, Qt.PenStyle.DashLine),
        )
        self._add_text(col1_x + 18, common_row_y - 10, "Pump / Supply", size=10)
        self._add_text(col1_x + 18, common_row_y + 105, "Click pump to actuate", size=10, color="#1f77b4")

        # First row / third column: movement message
        self.scene.addRect(
            QRectF(col3_x - 10, message_row_y, 500, valve_h - 20),
            QPen(QColor("#cccccc"), 1),
            QBrush(QColor("white")),
        )
        self._add_text(col3_x, message_row_y + 10, "Valve Movement Messages", size=12, bold=True)
        self._add_text(col3_x, message_row_y + 45, self.last_move_message, size=11, bold=True, color="#1f77b4")

        # Common close row
        self._draw_manifold_panel(
            x=col2_x,
            y=common_row_y,
            title="Common Close Line",
            manifold=self.sim.common_close_manifold,
            line_state=self.sim.common_close_line.state.value,
            returns=self.common_close_returns,
            common=True,
            index=None,
            width=manifold_w,
            height=manifold_h,
        )

        # Valve rows
        for i, valve in enumerate(self.sim.valves):
            y = common_row_y + row_height * (i + 1)

            self._draw_manifold_panel(
                x=col2_x,
                y=y,
                title=f"Open Line {i + 1}",
                manifold=self.sim.manifolds[i],
                line_state=self.sim.lines[i].state.value,
                returns=self.open_returns[i],
                common=False,
                index=i,
                width=manifold_w,
                height=manifold_h,
            )

            self._draw_valve_svg(
                x=col3_x,
                y=y,
                position=valve.choke.value,
                width=valve_w,
                height=valve_h,
            )

            self._draw_valve_info(
                x=col4_x,
                y=y,
                valve_number=i + 1,
                position=valve.choke.value,
                line_state=self.sim.lines[i].state.value,
                returns=self.open_returns[i],
                box_w=280,
                box_h=120,
            )

    def _draw_manifold_panel(
        self,
        x: int,
        y: int,
        title: str,
        manifold,
        line_state: str,
        returns: int,
        common: bool,
        index: int | None,
        width: int,
        height: int,
    ) -> None:
        pixmap = self._get_manifold_pixmap(manifold, width, height)

        item = QGraphicsPixmapItem(pixmap)
        item.setPos(x, y)
        self.scene.addItem(item)

        self._add_text(x + width + 20, y + 10, title, size=12, bold=False)
        self._add_text(x + width + 20, y + 42, f"Line: {line_state}", size=11)
        self._add_text(x + width + 20, y + 74, f"Returns: {returns}", size=11)

        block_box = (x + 58, y + 8, 97, 36)
        bleed_box = (x + 58, y + 58, 97, 36)

        green_pen = QPen(QColor("#2ca02c"), 2)
        green_brush = QBrush(QColor(204, 255, 204, 70))

        red_pen = QPen(QColor("#d62728"), 2)
        red_brush = QBrush(QColor(255, 214, 214, 70))

        if common:
            block_item = ClickableRectItem(
                block_box[0], block_box[1], block_box[2], block_box[3],
                lambda: self.toggle_common("block"),
                green_pen,
                green_brush,
            )
            bleed_item = ClickableRectItem(
                bleed_box[0], bleed_box[1], bleed_box[2], bleed_box[3],
                lambda: self.toggle_common("bleed"),
                red_pen,
                red_brush,
            )
        else:
            assert index is not None
            block_item = ClickableRectItem(
                block_box[0], block_box[1], block_box[2], block_box[3],
                lambda i=index: self.toggle_open(i, "block"),
                green_pen,
                green_brush,
            )
            bleed_item = ClickableRectItem(
                bleed_box[0], bleed_box[1], bleed_box[2], bleed_box[3],
                lambda i=index: self.toggle_open(i, "bleed"),
                red_pen,
                red_brush,
            )

        self.scene.addItem(block_item)
        self.scene.addItem(bleed_item)

        self._add_text(block_box[0] + 18, block_box[1] - 16, "BLOCK", size=9, bold=True, color="#2ca02c")
        self._add_text(bleed_box[0] + 18, bleed_box[1] - 16, "BLEED", size=9, bold=True, color="#d62728")

    def _draw_valve_svg(self, x: int, y: int, position: str, width: int, height: int) -> None:
        pixmap = self._get_valve_pixmap(position, width, height)
        item = QGraphicsPixmapItem(pixmap)
        item.setPos(x, y)
        self.scene.addItem(item)

    def _draw_valve_info(
        self,
        x: int,
        y: int,
        valve_number: int,
        position: str,
        line_state: str,
        returns: int,
        box_w: int,
        box_h: int,
    ) -> None:
        self.scene.addRect(
            QRectF(x, y + 10, box_w, box_h),
            QPen(QColor("#cccccc"), 1),
            QBrush(QColor("white")),
        )
        self._add_text(x + 15, y + 22, f"FCV-{valve_number}", size=12, bold=True)
        self._add_text(x + 15, y + 50, f"Position: {position}", size=11)
        self._add_text(x + 15, y + 78, f"Open Line: {line_state}", size=11)
        self._add_text(x + 15, y + 106, f"Returns: {returns}", size=11)

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

    def _render_svg_to_pixmap(self, path: Path, width: int, height: int) -> QPixmap:
        key = (str(path), width, height)

        if key not in self.pixmap_cache:
            if not path.exists():
                raise FileNotFoundError(f"Could not find SVG asset: {path}")

            renderer = QSvgRenderer(str(path))
            if not renderer.isValid():
                raise ValueError(f"Invalid SVG file: {path}")

            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            renderer.render(painter, QRectF(0, 0, width, height))
            painter.end()

            self.pixmap_cache[key] = pixmap

        return self.pixmap_cache[key]

    def _get_manifold_pixmap(self, manifold, width: int, height: int) -> QPixmap:
        block = "open" if manifold.block == ValveState.OPEN else "close"
        bleed = "open" if manifold.bleed == ValveState.OPEN else "close"
        filename = MANIFOLD_ASSETS[(block, bleed)]
        path = ASSET_DIR / filename
        return self._render_svg_to_pixmap(path, width, height)

    def _get_valve_pixmap(self, position: str, width: int, height: int) -> QPixmap:
        filename = VALVE_ASSETS.get(position)
        if filename is None:
            raise KeyError(f"No SVG mapping for valve position: {position}")
        path = ASSET_DIR / filename
        return self._render_svg_to_pixmap(path, width, height)

    def _get_pump_pixmap(self, width: int, height: int) -> QPixmap:
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


def main() -> None:
    app = QApplication([])
    window = ValveSimulatorUI()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
