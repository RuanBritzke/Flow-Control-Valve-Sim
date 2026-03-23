from hydraulics import ValveState
from simulator import ValveSimulator


def print_help() -> None:
    print("""
Commands:
  actuate
  state
  list
  add-valve
  help
  quit

Panel commands:
  common-close.block.open
  common-close.block.close
  common-close.bleed.open
  common-close.bleed.close

  open-<valve_number>.block.open
  open-<valve_number>.block.close
  open-<valve_number>.bleed.open
  open-<valve_number>.bleed.close
""")


def set_valve_state(target, part: str, state: str) -> None:
    value = {
        "open": ValveState.OPEN,
        "close": ValveState.CLOSED,
    }.get(state)

    if value is None:
        raise ValueError(f"Invalid state: {state}")
    
    if part == "block":
        target.block = value
    elif part == "bleed":
        target.bleed = value
    else:
        raise ValueError(f"Invalid part: {part}")


def apply_panel_command(sim: ValveSimulator, cmd: str) -> bool:
    try:
        target_name, part, action = cmd.strip().lower().split(".")
    except ValueError:
        print("Invalid command format. Use 'target.part.action'.")
        return False

    if part not in ("block", "bleed"):
        print("Invalid part. Use 'block' or 'bleed'.")
        return False

    if action not in ("open", "close"):
        print("Invalid action. Use 'open' or 'close'.")
        return False

    if target_name == "common-close":
        target = sim.common_close_manifold

    elif target_name.startswith("open-"):
        try:
            valve_number = int(target_name.split("-")[1])
        except (IndexError, ValueError):
            print("Invalid open manifold target. Use 'open-1', 'open-2', etc.")
            return False

        index = valve_number - 1

        if index < 0 or index >= len(sim.manifolds):
            print(f"Open manifold {valve_number} does not exist.")
            return False

        target = sim.manifolds[index]

    else:
        print("Invalid target. Use 'common-close' or 'open-N'.")
        return False

    try:
        set_valve_state(target, part, action)
    except ValueError as e:
        print(e)
        return False

    return True


def print_actuation_results(results) -> None:
    print("\n--- ACTUATION RESULTS ---")
    for i, result in enumerate(results, start=1):
        command = result.command.value if result.command else None
        print(
            f"Valve {i}: "
            f"movement={result.movement}, "
            f"old={result.old_position.value}, "
            f"new={result.new_position.value}, "
            f"command={command}, "
            f"returns={result.fluid_returns}"
        )
    print("-------------------------\n")

def print_valve_list(sim: ValveSimulator) -> None:
    print("\n--- INSTALLED VALVES ---")
    for i, _ in enumerate(sim.valves, start=1):
        print(f"FCV {i}")
    print("-------------------------\n")

def main() -> None:
    sim = ValveSimulator()

    print("Welcome to the Valve Simulator!")
    print_help()
    sim.print_state()

    while True:
        cmd = input(">> ").strip().lower()

        if cmd == "quit":
            break

        elif cmd == "help":
            print_help()

        elif cmd == "state":
            sim.print_state()

        elif cmd == "list":
            print_valve_list(sim)

        elif cmd == "add-valve":
            sim.add_valve()
            print(f"FCV-{len(sim.valves)} added.")
            sim.print_state()

        elif cmd == "actuate":
            results = sim.actuate()
            print_actuation_results(results)
            sim.print_state()

        elif apply_panel_command(sim, cmd):
            sim.print_state()

        else:
            print("Unknown command. Type 'help' for a list of commands.")


if __name__ == "__main__":
    main()