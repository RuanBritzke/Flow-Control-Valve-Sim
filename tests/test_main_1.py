from cli import set_valve_state, apply_panel_command
from simulator import ValveSimulator
from hydraulics.pressure_objects import ValveState


def test_set_valve_state_block_open():
    sim = ValveSimulator()

    set_valve_state(sim.manifolds[0], "block", "open")

    assert sim.manifolds[0].block == ValveState.OPEN


def test_set_valve_state_bleed_close():
    sim = ValveSimulator()

    set_valve_state(sim.manifolds[0], "bleed", "close")

    assert sim.manifolds[0].bleed == ValveState.CLOSED


def test_apply_common_close_command():
    sim = ValveSimulator()

    handled = apply_panel_command(sim, "common-close.block.close")

    assert handled is True
    assert sim.common_close_manifold.block == ValveState.CLOSED


def test_apply_open_1_command():
    sim = ValveSimulator()

    handled = apply_panel_command(sim, "open-1.bleed.close")

    assert handled is True
    assert sim.manifolds[0].bleed == ValveState.CLOSED


def test_apply_invalid_open_index():
    sim = ValveSimulator()

    handled = apply_panel_command(sim, "open-99.block.open")

    assert handled is False


def test_apply_invalid_format():
    sim = ValveSimulator()

    handled = apply_panel_command(sim, "bad-command")

    assert handled is False