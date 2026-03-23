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
        # these are unique objects that are going to be shared by all other elements
        self.panel = ManifoldPanel()

        # these are the commom_close line and block, they are connected to all FlowControlValve close_port
        self.common_close_manifold = BlockAndBleed()
        self.common_close_line = Line()

        # The idea is that each item of the list corresponds to the one FlowControlValve
        self.manifolds: List[BlockAndBleed] = []
        self.lines: List[Line] = []
        self.valves: List[FlowControlValve] = []

        # Connecting lines to BlockAndBleed Manifolds, and BlockAndBleed manifolds to the ManifoldPanel
        self.panel.connect(
            self.common_close_manifold, self.common_close_line
        )  # commom_close line and commom_close manifold
        self.add_valve()

    def add_valve(self) -> None:
        self.manifolds.append(BlockAndBleed())
        self.lines.append(Line())
        self.panel.connect(
            self.manifolds[-1], self.lines[-1]
        )  # Connect new manifold to new line
        self.valves.append(
            FlowControlValve(self.lines[-1], self.common_close_line)
        )  # Connect new valve to new line and commom_close line

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

if __name__ == "__main__":
    def print_results(results, expected=None) -> None:
        for i, result in enumerate(results, start=1):
            print(
                f"  Valve {i} -> movement: {result.movement}, "
                f"new_position: {result.new_position.value}"
            )
            if expected is not None:
                exp_move, exp_pos = expected[i - 1]
                passed = (
                    result.movement == exp_move
                    and result.new_position.value == exp_pos
                )
                print(
                    f"    Expected: movement={exp_move}, new_position={exp_pos}"
                )
                print(f"    Test {'PASSED' if passed else 'FAILED'}")

    sim = ValveSimulator()
    print("=== ValveSimulator self-test ===")
    sim.print_state()

    print("Test 1: Actuate with initial conditions")
    results = sim.actuate()
    print_results(results, expected=[(False, "Fully Closed")])
    print()

    print("Test 2: Configure valve 1 to open")
    sim.manifolds[0].block = ValveState.OPEN
    sim.manifolds[0].bleed = ValveState.CLOSED
    sim.common_close_manifold.block = ValveState.CLOSED
    sim.common_close_manifold.bleed = ValveState.OPEN

    sim.print_state()
    results = sim.actuate()
    print_results(results, expected=[(True, "5")])
    print()

    # isolate valve 1 again
    sim.manifolds[0].block = ValveState.CLOSED
    sim.manifolds[0].bleed = ValveState.OPEN

    print("Test 3: Add valves 2 and 3")
    sim.add_valve()
    sim.add_valve()
    sim.print_state()

    print("Test 4: Open valve 2 only")
    sim.manifolds[1].block = ValveState.OPEN
    sim.manifolds[1].bleed = ValveState.CLOSED

    results = sim.actuate()
    print_results(
        results,
        expected=[
            (False, "5"),
            (True, "5"),
            (False, "Fully Closed"),
        ],
    )
    print()

    # isolate valve 2 again
    sim.manifolds[1].block = ValveState.CLOSED
    sim.manifolds[1].bleed = ValveState.OPEN

    print("Test 5: Open valve 3 only")
    sim.manifolds[2].block = ValveState.OPEN
    sim.manifolds[2].bleed = ValveState.CLOSED

    results = sim.actuate()
    print_results(
        results,
        expected=[
            (False, "5"),
            (False, "5"),
            (True, "5"),
        ],
    )
    print()

    # isolate valve 3 again
    sim.manifolds[2].block = ValveState.CLOSED
    sim.manifolds[2].bleed = ValveState.OPEN

    print("Test 6: Close all valves together")
    sim.common_close_manifold.block = ValveState.OPEN
    sim.common_close_manifold.bleed = ValveState.CLOSED

    results = sim.actuate()
    sim.print_state()
    print_results(
        results,
        expected=[
            (True, "1"),
            (True, "1"),
            (True, "1"),
        ],
    )
    print()

    # restore default common close
    sim.common_close_manifold.block = ValveState.CLOSED
    sim.common_close_manifold.bleed = ValveState.OPEN

    print("=== End of self-test ===")