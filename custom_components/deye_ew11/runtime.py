"""Battery runtime estimate for the Battery Runtime sensor (pure, no Home Assistant imports)."""
from __future__ import annotations

# Same rules as the energy flow card: under 10 W the battery is idle, and at 99-100% SOC
# a top-up under 100 W is the inverter maintaining charge, not "charging to full".
IDLE_W = 10
FULL_SOC = 99
TOPUP_W = 100
MIN_LOAD_W = 50


def battery_runtime(soc, battery_power, load_power, capacity_kwh):
    """Return (mode, hours) or None when there is nothing meaningful to show.

    battery_power is negative while charging and positive while discharging (W).
    mode: "charge"    - time to full at the current charge power;
          "discharge" - time to empty at the current discharge power;
          "reserve"   - how long the current home load would run from the battery.
    """
    if not capacity_kwh or capacity_kwh <= 0 or soc is None:
        return None
    soc = max(0.0, min(100.0, float(soc)))
    bat = float(battery_power or 0)
    load = float(load_power or 0)
    total_wh = capacity_kwh * 1000
    stored_wh = total_wh * soc / 100

    topping_up = soc >= FULL_SOC and -bat < TOPUP_W
    if bat < -IDLE_W and soc < 100 and not topping_up:
        mode, hours = "charge", (total_wh - stored_wh) / -bat
    elif bat > IDLE_W:
        mode, hours = "discharge", stored_wh / bat
    elif load > MIN_LOAD_W:
        mode, hours = "reserve", stored_wh / load
    else:
        return None
    return (mode, hours) if hours > 0 else None


def format_hours(hours):
    """'45 хв', '3 год', '25 год 33 хв'; never '0 хв'."""
    minutes = max(1, round(hours * 60))
    h, m = divmod(minutes, 60)
    if not h:
        return f"{m} хв"
    return f"{h} год {m} хв" if m else f"{h} год"
