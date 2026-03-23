from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import List

class ValveState(Enum):
    OPEN = "Open"
    CLOSED = "Closed"

class LineState(Enum):
    #TODO: maybe i want to add the @property decorator here so I can make the FlowControlValve detect change in the line state.
    # but for now, let's keep it simple and just have the FlowControlValve call panel.pressurize() after every step to update the line states.    
    PRESSURIZED = "Pressurized"
    VENTED = "Vented"
    TRAPPED = "Trapped"

@dataclass
class Line:
    state: LineState = LineState.VENTED

@dataclass
class BlockAndBleed:
    def __init__(self, block : ValveState = ValveState.OPEN, bleed : ValveState = ValveState.OPEN):
        self._block = block
        self._bleed = bleed
        self.line = None

    @property
    def block(self) -> ValveState:
        return self._block
    
    @block.setter
    def block(self, value: ValveState) -> None:
        self._block = value
        self._update_line()

    @property
    def bleed(self) -> ValveState:
        return self._bleed
    
    @bleed.setter
    def bleed(self, value: ValveState) -> None:
        self._bleed = value
        self._update_line()

    def _update_line(self) -> None:
        if self.line is None:
            return
        
        if self._bleed == ValveState.OPEN:
            self.line.state = LineState.VENTED
        elif self._block == ValveState.CLOSED:
            self.line.state = LineState.TRAPPED

    def pressure_route(self) -> LineState:
        # bleed open vents regardless
        if self.bleed == ValveState.OPEN:
            return LineState.VENTED

        # bleed closed
        if self.block == ValveState.OPEN:
            return LineState.PRESSURIZED

        return LineState.TRAPPED

class ManifoldPanel:
    def __init__(self) -> None:
        self.ports: List[BlockAndBleed] = []

    def connect(self, manifold: BlockAndBleed, line: Line) -> None:
        manifold.line = line
        self.ports.append(manifold)

    def pressurize(self) -> None:
        for manifold in self.ports:
            if manifold.line is not None:
                manifold.line.state = manifold.pressure_route()

if __name__ == "__main__":
    def print_case(label: str, manifold: BlockAndBleed, expected: LineState) -> None:
        result = manifold.pressure_route()
        print(f"\n{label}")
        print(f"    Block   : {manifold.block.value}")
        print(f"    Bleed   : {manifold.bleed.value}");
        print(f"    Result  : {result.value}");
        print(f"    Expected: {expected.value}")
        print(f"    Test {'PASSED' if result == expected else 'FAILED'}")

    print("=== pressure_objects.py self-test ===");

    # Test 1: Bleed Open -> should always vent
    m = BlockAndBleed(block=ValveState.OPEN, bleed=ValveState.OPEN)
    print_case("Test 1: Block Open, Bleed Open", m, LineState.VENTED)

    m = BlockAndBleed(block=ValveState.CLOSED, bleed=ValveState.OPEN)
    print_case("Test 1b: Block Closed, Bleed Open", m, LineState.VENTED)

    # Test 2: Bleed Closed, Block Open -> should pressurize (no need for supply here)
    m = BlockAndBleed(block=ValveState.OPEN, bleed=ValveState.CLOSED)
    print_case("Test 2: Block Open, Bleed Closed", m, LineState.PRESSURIZED)

    # Test 3: Bleed Closed, Block Closed -> should trap
    m = BlockAndBleed(block=ValveState.CLOSED, bleed=ValveState.CLOSED)
    print_case("Test 3: Block Closed, Bleed Closed", m, LineState.TRAPPED)

    # Test 4: panel test (withotu pump)
    panel = ManifoldPanel()

    m1 = BlockAndBleed(block=ValveState.OPEN, bleed=ValveState.CLOSED) # should pressurize
    m2 = BlockAndBleed(block=ValveState.CLOSED, bleed=ValveState.OPEN) # should vent
    m3 = BlockAndBleed(block=ValveState.CLOSED, bleed=ValveState.CLOSED) # should trap

    l1 = Line()
    l2 = Line()
    l3 = Line()

    panel.connect(m1, l1)
    panel.connect(m2, l2)
    panel.connect(m3, l3)

    panel.pressurize()

    print("\nTest 4: Panel Integration")
    print_case("Port 1", m1, LineState.PRESSURIZED)
    print_case("Port 2", m2, LineState.VENTED)
    print_case("Port 3", m3, LineState.TRAPPED)

    # Test 5: property setters update connected line immediately
    print("\nTest 5: Property side-effects")

    m4 = BlockAndBleed(block=ValveState.OPEN, bleed=ValveState.CLOSED)
    l4 = Line()
    panel.connect(m4, l4)

    m4.bleed = ValveState.OPEN
    print(f"    After opening bleed  : {l4.state.value}")
    print(f"    Expected             : {LineState.VENTED.value}")
    print(f"    Test {'PASSED' if l4.state == LineState.VENTED else 'FAILED'}")

    m4.bleed = ValveState.CLOSED
    m4.block = ValveState.CLOSED
    print(f"    After closing block  : {l4.state.value}")
    print(f"    Expected             : {LineState.TRAPPED.value}")
    print(f"    Test {'PASSED' if l4.state == LineState.TRAPPED else 'FAILED'}")

    print("\n=== pressure_objects.py self-test complete ===")