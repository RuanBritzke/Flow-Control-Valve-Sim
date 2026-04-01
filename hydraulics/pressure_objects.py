from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import List

class ValveState(Enum):
    OPEN = "Open"
    CLOSED = "Closed"

class LineState(Enum):
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
