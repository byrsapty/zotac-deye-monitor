"""Checks for the battery runtime estimate. Run: python tests/test_runtime.py"""
import importlib.util
from pathlib import Path

# Load the module by path: importing the package would pull in Home Assistant
_spec = importlib.util.spec_from_file_location(
    "runtime", Path(__file__).resolve().parents[1] / "custom_components" / "deye_ew11" / "runtime.py"
)
runtime = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runtime)
br, fh = runtime.battery_runtime, runtime.format_hours


def test_full_battery_topping_up_shows_reserve():
    # The reported case: 100%, inverter tops up ~23 W, home 1 kW -> reserve, not "0 хв" to full
    assert br(100, -23, 1000, 16) == ("reserve", 16.0)
    assert br(99, -60, 800, 16)[0] == "reserve"


def test_charging():
    mode, h = br(78, -620, 1940, 16)
    assert mode == "charge" and abs(h - 3520 / 620) < 1e-9
    # strong charge at 99% is still charging; at 100% there is nothing left to charge
    assert br(99, -1500, 500, 16)[0] == "charge"
    assert br(100, -150, 500, 16)[0] == "reserve"


def test_discharge_uses_battery_power_not_load():
    mode, h = br(64, 1700, 2500, 16)  # sun covers part of the 2.5 kW load
    assert mode == "discharge" and abs(h - 10240 / 1700) < 1e-9


def test_nothing_to_show():
    assert br(100, 0, 30, 16) is None       # idle, no meaningful load
    assert br(50, -500, 1000, 0) is None    # capacity not configured
    assert br(None, -500, 1000, 16) is None
    assert br(0, 300, 300, 16) is None      # empty battery: 0 hours is not shown


def test_format():
    assert fh(0.001) == "1 хв"
    assert fh(0.75) == "45 хв"
    assert fh(3.0) == "3 год"
    assert fh(25.55) == "25 год 33 хв"
    assert fh(59.5 / 60) == "1 год"  # rounds to a whole hour, not "60 хв"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
