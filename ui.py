import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw

from simulator import ValveSimulator
from hydraulics import ValveState


ASSET_DIR = Path(__file__).resolve().parent / "assets"

MANIFOLD_ASSETS = {
    ("open", "open"): "BlockAndBleed-open-open.png",
    ("open", "close"): "BlockAndBleed-open-close.png",
    ("close", "open"): "BlockAndBleed-close-open.png",
    ("close", "close"): "BlockAndBleed-close-close.png",
}


class ValveSimulatorUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Hydraulic Valve Simulator")
        self.root.geometry("1300x900")

        self.sim = ValveSimulator()

        self.status_var = tk.StringVar(value="Ready")
        self.image_cache: dict[tuple[str, int, int], ImageTk.PhotoImage] = {}

        self.common_close_returns = 0
        self.open_returns: list[int] = [0 for _ in self.sim.valves]

        top = tk.Frame(self.root)
        top.pack(fill="x", padx=10, pady=10)

        tk.Button(top, text="Add Valve", command=self.add_valve).pack(side="left", padx=4)
        tk.Label(top, textvariable=self.status_var).pack(side="left", padx=12)

        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(fill="both", expand=True)

        self.redraw()

    def add_valve(self) -> None:
        self.sim.add_valve()
        self.open_returns.append(0)
        self.status_var.set(f"FCV-{len(self.sim.valves)} added")
        self.redraw()

    def actuate(self) -> None:
        results = self.sim.actuate()

        moved = []
        for i, result in enumerate(results, start=1):
            if result.movement:
                moved.append(f"FCV-{i}")

            if result.return_line is self.sim.common_close_line:
                self.common_close_returns = result.fluid_returns or 0

            for j, line in enumerate(self.sim.lines):
                if result.return_line is line:
                    self.open_returns[j] = result.fluid_returns or 0
                    break

        self.status_var.set("Moved: " + ", ".join(moved) if moved else "No valve movement")
        self.redraw()

    def redraw(self) -> None:
        self.canvas.delete("all")

        top_y = 110
        left_x = 70
        trunk_x = 250
        manifold_x = 300
        fcv_x = 1080
        row_h = 170

        self.canvas.create_text(
            40,
            35,
            anchor="w",
            text="Hydraulic Valve Simulator",
            font=("Segoe UI", 16, "bold"),
        )

        # Pump drawing as the actuate button
        pump_img = self._get_pump_image(width=110, height=70)
        pump_x = left_x
        pump_y = top_y - 35

        self.canvas.create_text(pump_x - 10, pump_y - 18, anchor="w", text="Pump / Supply")
        self.canvas.create_image(pump_x, pump_y, image=pump_img, anchor="nw", tags=("pump",))
        self.canvas.create_rectangle(
            pump_x,
            pump_y,
            pump_x + 110,
            pump_y + 70,
            outline="#1f77b4",
            width=2,
            dash=(4, 2),
            tags=("pump",),
        )
        self.canvas.create_text(
            pump_x + 55,
            pump_y + 84,
            text="Click pump to actuate",
            fill="#1f77b4",
        )
        self.canvas.tag_bind("pump", "<Button-1>", lambda e: self.actuate())

        # line from pump to common row
        self.canvas.create_line(pump_x + 110, top_y, manifold_x, top_y, width=2)

        # shared supply trunk
        last_y = top_y + row_h * max(1, len(self.sim.valves))
        self.canvas.create_line(trunk_x, top_y, trunk_x, last_y, width=2)

        # common close row
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

        # valve rows
        for i, valve in enumerate(self.sim.valves):
            y = top_y + row_h * (i + 1)
            self.canvas.create_line(trunk_x, y, manifold_x, y, width=2)

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
        image = self._get_manifold_image(manifold, width=240, height=120)
        img_w = image.width()
        img_h = image.height()

        self.canvas.create_image(manifold_x, y - 10, image=image, anchor="nw")
        self.canvas.create_text(manifold_x + img_w + 10, y + 5, anchor="w", text=title, font=("Segoe UI", 12))
        self.canvas.create_text(manifold_x + img_w + 10, y + 30, anchor="w", text=f"Line: {line_state}")
        self.canvas.create_text(manifold_x + img_w + 10, y + 55, anchor="w", text=f"Returns: {returns}")

        line_y = y + 45
        line_start = manifold_x + img_w - 5
        line_end = (fcv_x - 20) if fcv_x is not None else 1030
        self.canvas.create_line(line_start, line_y, line_end, line_y, width=2, arrow=tk.LAST)

        # Visible learning hotspots
        block_box = (manifold_x + 58, y + 5, manifold_x + 155, y + 42)
        bleed_box = (manifold_x + 58, y + 58, manifold_x + 155, y + 96)

        if common:
            self.canvas.create_rectangle(
                *block_box, outline="#2ca02c", width=2, fill="#ccffcc", stipple="gray25", tags=("common-block",)
            )
            self.canvas.create_rectangle(
                *bleed_box, outline="#d62728", width=2, fill="#ffd6d6", stipple="gray25", tags=("common-bleed",)
            )
            self.canvas.create_text(
                (block_box[0] + block_box[2]) / 2,
                block_box[1] - 10,
                text="BLOCK",
                fill="#2ca02c",
                font=("Segoe UI", 9, "bold"),
            )
            self.canvas.create_text(
                (bleed_box[0] + bleed_box[2]) / 2,
                bleed_box[1] - 10,
                text="BLEED",
                fill="#d62728",
                font=("Segoe UI", 9, "bold"),
            )
            self.canvas.tag_bind("common-block", "<Button-1>", lambda e: self.toggle_common("block"))
            self.canvas.tag_bind("common-bleed", "<Button-1>", lambda e: self.toggle_common("bleed"))
        else:
            assert index is not None
            block_tag = f"open-{index}-block"
            bleed_tag = f"open-{index}-bleed"

            self.canvas.create_rectangle(
                *block_box, outline="#2ca02c", width=2, fill="#ccffcc", stipple="gray25", tags=(block_tag,)
            )
            self.canvas.create_rectangle(
                *bleed_box, outline="#d62728", width=2, fill="#ffd6d6", stipple="gray25", tags=(bleed_tag,)
            )
            self.canvas.create_text(
                (block_box[0] + block_box[2]) / 2,
                block_box[1] - 10,
                text="BLOCK",
                fill="#2ca02c",
                font=("Segoe UI", 9, "bold"),
            )
            self.canvas.create_text(
                (bleed_box[0] + bleed_box[2]) / 2,
                bleed_box[1] - 10,
                text="BLEED",
                fill="#d62728",
                font=("Segoe UI", 9, "bold"),
            )

            self.canvas.tag_bind(block_tag, "<Button-1>", lambda e, i=index: self.toggle_open(i, "block"))
            self.canvas.tag_bind(bleed_tag, "<Button-1>", lambda e, i=index: self.toggle_open(i, "bleed"))

    def _draw_fcv(self, x: int, y: int, label: str, position: str) -> None:
        self.canvas.create_rectangle(x, y + 10, x + 35, y + 110, width=1)
        self.canvas.create_rectangle(x + 8, y + 20, x + 20, y + 42, width=1)
        self.canvas.create_rectangle(x + 8, y + 80, x + 20, y + 102, width=1)
        self.canvas.create_text(x + 45, y + 25, anchor="w", text=label, font=("Segoe UI", 11))
        self.canvas.create_text(x + 45, y + 50, anchor="w", text=f"Pos: {position}", font=("Segoe UI", 10))

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

    def _get_pump_image(self, width=110, height=70) -> ImageTk.PhotoImage:
        key = ("__pump__", width, height)
        if key not in self.image_cache:
            image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
            draw = ImageDraw.Draw(image)
            draw.ellipse((8, 12, 52, 56), outline="black", width=2)
            draw.polygon([(40, 34), (28, 24), (28, 44)], fill="black")
            draw.line((52, 34, width - 8, 34), fill="black", width=4)
            self.image_cache[key] = ImageTk.PhotoImage(image)
        return self.image_cache[key]

    def _get_manifold_image(self, manifold, width=240, height=120) -> ImageTk.PhotoImage:
        block = "open" if manifold.block == ValveState.OPEN else "close"
        bleed = "open" if manifold.bleed == ValveState.OPEN else "close"
        filename = MANIFOLD_ASSETS[(block, bleed)]
        path = ASSET_DIR / filename

        key = (str(path), width, height)
        if key not in self.image_cache:
            with Image.open(path) as image:
                image = image.resize((width, height), Image.LANCZOS)
                self.image_cache[key] = ImageTk.PhotoImage(image)

        return self.image_cache[key]


def main() -> None:
    root = tk.Tk()
    ValveSimulatorUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()