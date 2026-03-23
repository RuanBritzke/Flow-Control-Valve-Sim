from cli import print_help, print_actuation_results
from trfc.flow_control_valve import FCVTransitionResult, Position, Command


def test_print_help(capsys):
    print_help()
    out = capsys.readouterr().out

    assert "actuate" in out
    assert "add-valve" in out
    assert "common-close.block.open" in out


def test_print_actuation_results(capsys):
    results = [
        FCVTransitionResult(
            movement=True,
            old_position=Position.p1,
            new_position=Position.p2,
            command=Command.valve_open,
            fluid_returns=364,
            return_line=None,
        )
    ]

    print_actuation_results(results)
    out = capsys.readouterr().out

    assert "Valve 1" in out
    assert "movement=True" in out
    assert "old=Fully Closed" in out
    assert "new=5" in out