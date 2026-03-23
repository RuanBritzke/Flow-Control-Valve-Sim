from enum import Enum
from typing import Dict, Tuple, Optional
from hydraulics import Line, LineState
from dataclasses import dataclass


class Position(str, Enum):
    p1 = "Fully Closed"
    p2 = "5"
    p3 = "1"
    p4 = "6"
    p5 = "2"
    p6 = "7"
    p7 = "3"
    p8 = "8"
    p9 = "4"
    p10 = "Fully Open"


class Command(str, Enum):
    valve_open = "Open"
    valve_close = "Close"


# the transitions between the valve positons (current position, command needed): next position
transitions: Dict[Tuple[Position, Command], Tuple[Position, int]] = {
    (Position.p1, Command.valve_open): (Position.p2, 364),
    (Position.p2, Command.valve_close): (Position.p3, 120),
    (Position.p3, Command.valve_open): (Position.p4, 150),
    (Position.p4, Command.valve_close): (Position.p5, 120),
    (Position.p5, Command.valve_open): (Position.p6, 150),
    (Position.p6, Command.valve_close): (Position.p7, 120),
    (Position.p7, Command.valve_open): (Position.p8, 150),
    (Position.p8, Command.valve_close): (Position.p9, 120),
    (Position.p9, Command.valve_open): (Position.p10, 150),
    (Position.p10, Command.valve_close): (Position.p1, 538),
}

# choke opening percentage
choke_values: Dict[Position, float] = {
    Position.p1: 0.0000,
    Position.p2: 0.0076,
    Position.p3: 0.0152,
    Position.p4: 0.0228,
    Position.p5: 0.0305,
    Position.p6: 0.0457,
    Position.p7: 0.0686,
    Position.p8: 0.0991,
    Position.p9: 0.1370,
    Position.p10: 1.000,
}


@dataclass
class FCVTransitionResult:
    movement: bool
    old_position: Position
    new_position: Position
    command: Optional[Command]
    fluid_returns: Optional[int]
    return_line: Optional[Line]


class FlowControlValve:
    def __init__(self, open_port: Line, close_port: Line) -> None:
        self.choke: Position = Position.p1
        self.open_port = open_port
        self.close_port = close_port

    def update(self) -> FCVTransitionResult:
        old_position = self.choke
        if (
            self.open_port.state == LineState.PRESSURIZED
            and self.close_port.state == LineState.VENTED
        ):
            cmd = Command.valve_open
            return_line = self.close_port
        elif (
            self.open_port.state == LineState.VENTED
            and self.close_port.state == LineState.PRESSURIZED
        ):
            cmd = Command.valve_close
            return_line = self.open_port
        else:
            return FCVTransitionResult(
                movement=False,
                old_position=old_position,
                new_position=old_position,
                command=None,
                fluid_returns=0,
                return_line=None,
            )
        transition = transitions.get((self.choke, cmd))
        if transition is None:
            return FCVTransitionResult(
                movement=False,
                old_position=old_position,
                new_position=old_position,
                command=None,
                fluid_returns=0,
                return_line=None,
            )

        new_position, returns = transition
        self.choke = new_position

        return FCVTransitionResult(
            movement=True,
            old_position=old_position,
            new_position=new_position,
            command=cmd,
            fluid_returns=returns,
            return_line=return_line,
        )

    def get_choke(self) -> Position:
        return self.choke

if __name__ == "__main__":
    def print_result(label: str, result: FCVTransitionResult, valve: FlowControlValve) -> None:
        print(f"\n{label}")
        print(f"  movement      : {result.movement}")
        print(f"  old_position : {result.old_position.value}")
        print(f"  new_position : {result.new_position.value}")
        print(f"  command      : {result.command.value if result.command else None}")
        print(f"  returns      : {result.fluid_returns}")
        print(f"  return_line  : {'open_port' if result.return_line is valve.open_port else 'close_port' if result.return_line is valve.close_port else None}")
        print(f"  valve choke  : {choke_values[valve.get_choke().value] * 100:.2f}%")

    open_line = Line()
    close_line = Line()
    valve = FlowControlValve(open_line, close_line)

    print("=== FlowControlValve self-test ===")
    print(f"Initial position: {valve.get_choke().value}")

    # Test 1: invalid configurations -> should not move
    open_line.state = LineState.TRAPPED
    close_line.state = LineState.TRAPPED
    result = valve.step()
    print_result(f"Test 1: invalid line states - Open Port: {open_line.state.value}, Close Port: {close_line.state.value}", result, valve)

    # test 1b: invalid configuration -> should not move
    open_line.state = LineState.PRESSURIZED
    close_line.state = LineState.PRESSURIZED
    result = valve.step()
    print_result(f"Test 1b: invalid line states - Open Port: {open_line.state.value}, Close Port: {close_line.state.value}", result, valve)

    # test 1c: invalid configuration -> should not move
    open_line.state = LineState.VENTED
    close_line.state = LineState.VENTED
    result = valve.step()
    print_result(f"Test 1c: invalid line states - Open Port: {open_line.state.value}, Close Port: {close_line.state.value}", result, valve)

    # Test 2: opening sequence from p1 -> p2;
    open_line.state = LineState.PRESSURIZED
    close_line.state = LineState.VENTED
    result = valve.step()
    print_result("Test 2: open command", result, valve)

    # Test 3: closing sequence from p2 -> p3
    open_line.state = LineState.VENTED
    close_line.state = LineState.PRESSURIZED
    result = valve.step()
    print_result("Test 3: close command", result, valve)

    # Test 4: run full cycle until fully closed again
    print("\nTest 4: full cycle")
    while valve.get_choke() != Position.p1:
        open_line.state = LineState.PRESSURIZED
        close_line.state = LineState.VENTED
        result = valve.step()
        print_result("  step", result, valve)

        if not result.movement or valve.get_choke() == Position.p1:
            break

        open_line.state = LineState.VENTED
        close_line.state = LineState.PRESSURIZED
        result = valve.step()
        print_result("  step", result, valve)
        
        if not result.movement:
            break

    print("\n=== End of self-test ===")