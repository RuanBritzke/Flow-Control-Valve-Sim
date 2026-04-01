from hydraulics import BlockAndBleed, Line, ManifoldPanel, ValveState
from typing import List

from trfc.flow_control_valve import (
    FlowControlValve,
    FCVTransitionResult
)


def toggle_valve_state(value: ValveState) -> ValveState:
    return ValveState.CLOSED if value == ValveState.OPEN else ValveState.OPEN


class ValveSimulator:
    def __init__(self):
        self._build_initial_state()

    def _build_initial_state(self) -> None:
        # these are unique objects that are going to be shared by all other elements
        self.panel = ManifoldPanel()

        # these are the common_close line and block, they are connected to all FlowControlValve close_port
        self.common_close_manifold = BlockAndBleed()
        self.common_close_line = Line()

        # The idea is that each item of the list corresponds to one FlowControlValve
        self.manifolds: List[BlockAndBleed] = []
        self.lines: List[Line] = []
        self.valves: List[FlowControlValve] = []

        # Connecting lines to BlockAndBleed Manifolds, and BlockAndBleed manifolds to the ManifoldPanel
        self.panel.connect(
            self.common_close_manifold, self.common_close_line
        )  # common_close line and common_close manifold

        # initial simulator starts with one valve
        self.add_valve()

    def reset(self) -> None:
        self._build_initial_state()

    def add_valve(self) -> None:
        self.manifolds.append(BlockAndBleed())
        self.lines.append(Line())
        self.panel.connect(
            self.manifolds[-1], self.lines[-1]
        )  # Connect new manifold to new line
        self.valves.append(
            FlowControlValve(self.lines[-1], self.common_close_line)
        )  # Connect new valve to new line and common_close line

    def actuate(self) -> list[FCVTransitionResult]:
        self.panel.pressurize()  # Update line states based on manifold configurations
        return [valve.update() for valve in self.valves]

    def state_snapshot(self) -> dict:
        return {
            "common_close_manifold": {
                "block": self.common_close_manifold.block.value,
                "bleed": self.common_close_manifold.bleed.value,
            },
            "common_close_line": self.common_close_line.state.value,
            "valves": [
                {
                    "index": i,
                    "position": valve.choke.value,
                    "open_manifold": {
                        "block": self.manifolds[i].block.value,
                        "bleed": self.manifolds[i].bleed.value,
                    },
                    "open_line": self.lines[i].state.value,
                }
                for i, valve in enumerate(self.valves)
            ],
        }

    def print_state(self) -> None:
        s = self.state_snapshot()

        print("\n--- SYSTEM STATE ---")
        print(
            f"Common Close Manifold -> "
            f"Block: {s['common_close_manifold']['block']}, "
            f"Bleed: {s['common_close_manifold']['bleed']}"
        )
        print(f"Common Close Line -> {s['common_close_line']}")

        print("\nValves:")
        for valve in s["valves"]:
            print(
                f"  Valve {valve['index'] + 1} -> "
                f"Position: {valve['position']}"
            )
            print(
                f"    Open Manifold -> "
                f"Block: {valve['open_manifold']['block']}, "
                f"Bleed: {valve['open_manifold']['bleed']}"
            )
            print(f"    Open Line -> {valve['open_line']}")

        print("--------------------\n")
