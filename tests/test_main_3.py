from cli import main


def test_main_quit_immediately(monkeypatch, capsys):
    commands = iter(["quit"])
    monkeypatch.setattr("builtins.input", lambda _: next(commands))

    main()
    out = capsys.readouterr().out

    assert "Welcome to the Valve Simulator!" in out


def test_main_add_valve_then_quit(monkeypatch, capsys):
    commands = iter(["add-valve", "quit"])
    monkeypatch.setattr("builtins.input", lambda _: next(commands))

    main()
    out = capsys.readouterr().out

    assert "FCV-2 added." in out


def test_main_actuate_then_quit(monkeypatch, capsys):
    commands = iter([
        "common-close.block.close",
        "common-close.bleed.open",
        "open-1.block.open",
        "open-1.bleed.close",
        "actuate",
        "quit",
    ])
    monkeypatch.setattr("builtins.input", lambda _: next(commands))

    main()
    out = capsys.readouterr().out

    assert "--- ACTUATION RESULTS ---" in out
    assert "Valve 1:" in out