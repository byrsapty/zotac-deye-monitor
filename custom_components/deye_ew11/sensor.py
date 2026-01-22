"""Sensor platform with calculated sensors."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_BATTERY_CAPACITY, DEFAULT_BATTERY_CAPACITY, DOMAIN
from .coordinator import DeyeCoordinator

_LOGGER = logging.getLogger(__name__)

# Definition of all sensors
SENSOR_TYPES = [
    # Connection
    ("Connection Status", "connection", None, None, None, "mdi:connection", lambda d, c: "Connected" if d.get("connected") else "Disconnected"),
    
    # Battery
    ("Battery SOC", "battery_soc", PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, None, lambda d, c: d.get("battery_soc")),
    ("Battery Power", "battery_power", UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, None, lambda d, c: d.get("battery_power")),
    ("Battery Voltage", "battery_voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, None, lambda d, c: d.get("battery_voltage")),
    ("Battery Current", "battery_current", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, None, lambda d, c: d.get("battery_current")),
    ("Battery Temp", "battery_temp", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, None, lambda d, c: d.get("battery_temp")),
    
    # Temperatures
    ("DC Temperature", "dc_temp", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, None, lambda d, c: d.get("dc_temp")),
    ("AC Temperature", "ac_temp", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, None, lambda d, c: d.get("ac_temp")),
    
    # Grid
    ("Grid Voltage", "grid_voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, None, lambda d, c: d.get("grid_voltage")),
    ("Grid Frequency", "grid_freq", UnitOfFrequency.HERTZ, SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT, None, lambda d, c: d.get("grid_freq")),
    ("Load Frequency", "load_freq", UnitOfFrequency.HERTZ, SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT, None, lambda d, c: d.get("load_freq")),
    ("Grid Power", "grid_power", UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, None, lambda d, c: d.get("grid_power")),
    ("Inverter Current", "inverter_current", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, None, lambda d, c: d.get("inverter_current")),
    
    # Load
    ("Load Power", "load_power", UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, None, lambda d, c: d.get("load_power")),
    
    # Generator
    ("Generator Power", "gen_power", UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "mdi:engine", lambda d, c: d.get("gen_power", 0)),
    ("Generator Status", "gen_status", None, None, None, "mdi:engine-outline", lambda d, c: "Running" if d.get("gen_power", 0) > 50 else "Stopped"),
    
    # PV
    ("PV Power", "pv_power", UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "mdi:solar-power", lambda d, c: d.get("pv_power")),
    ("PV1 Power", "pv1_power", UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, None, lambda d, c: d.get("pv1_power")),
    ("PV2 Power", "pv2_power", UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, None, lambda d, c: d.get("pv2_power")),
    ("PV1 Voltage", "pv1_voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, None, lambda d, c: d.get("pv1_voltage")),
    ("PV1 Current", "pv1_current", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, None, lambda d, c: d.get("pv1_current")),
    ("PV2 Voltage", "pv2_voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, None, lambda d, c: d.get("pv2_voltage")),
    ("PV2 Current", "pv2_current", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, None, lambda d, c: d.get("pv2_current")),
    
    # Daily Energy
    ("Day Battery Charge", "day_battery_charge", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, None, lambda d, c: d.get("day_battery_charge")),
    ("Day Battery Discharge", "day_battery_discharge", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, None, lambda d, c: d.get("day_battery_discharge")),
    ("Day Grid Import", "day_grid_import", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, None, lambda d, c: d.get("day_grid_import")),
    ("Day Grid Export", "day_grid_export", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, None, lambda d, c: d.get("day_grid_export")),
    ("Day Load Energy", "day_load_energy", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, None, lambda d, c: d.get("day_load_energy")),
    ("Day PV Energy", "day_pv_energy", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, None, lambda d, c: d.get("day_pv_energy")),
    
    # Calculated sensors (NEW)
    ("Battery Capacity", "battery_capacity", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, None, "mdi:battery-sync", lambda d, c: c),
    ("Battery Remaining", "battery_remaining", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, None, "mdi:battery-charging", 
     lambda d, c: round((c * d.get("battery_soc", 0) / 100), 2) if c > 0 and d.get("battery_soc", 0) > 0 else 0),
    ("Battery Runtime", "battery_runtime", None, None, None, "mdi:clock-outline",
     lambda d, c: (
         (lambda val: 
              f"{int(val * 60)} хв" if val < 1 else 
              f"{int(val)} год {int((val % 1) * 60)} хв" if (val % 1) * 60 >= 1 else 
              f"{int(val)} год"
         )(
             # Inner logic: Standardize to HOURS first
             # If CHARGING (power > 0, POSITIVE): Time to FULL
             round(((c - (c * d.get("battery_soc", 0) / 100)) * 1000) / abs(d.get("battery_power", 1)), 2)
             if d.get("battery_power", 0) > 10 else 
             # If DISCHARGING (power < 0, NEGATIVE): Time to EMPTY
             round(((c * d.get("battery_soc", 0) / 100) * 1000) / d.get("load_power", 1), 2)
             if d.get("battery_power", 0) < -10 and d.get("load_power", 0) > 50 else 0
         )
     )),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor platform."""
    coordinator: DeyeCoordinator = hass.data[DOMAIN][entry.entry_id]
    battery_capacity = entry.data.get(CONF_BATTERY_CAPACITY, DEFAULT_BATTERY_CAPACITY)
    
    sensors = [
        DeyeSensor(coordinator, name, key, unit, device_class, state_class, icon, value_fn, battery_capacity)
        for name, key, unit, device_class, state_class, icon, value_fn in SENSOR_TYPES
    ]
    
    async_add_entities(sensors, True)
    _LOGGER.info("Added %d Deye sensors (battery capacity: %.2f kWh)", len(sensors), battery_capacity)


class DeyeSensor(CoordinatorEntity[DeyeCoordinator], SensorEntity):
    """Deye sensor entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DeyeCoordinator,
        name: str,
        key: str,
        unit: str | None,
        device_class: SensorDeviceClass | None,
        state_class: SensorStateClass | None,
        icon: str | None,
        value_fn,
        battery_capacity: float,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        if icon:
            self._attr_icon = icon
        self._key = key
        self._value_fn = value_fn
        self._battery_capacity = battery_capacity

    @property
    def native_value(self):
        """Return the state."""
        if not self.coordinator.data:
            return None
        return self._value_fn(self.coordinator.data, self._battery_capacity)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def device_info(self):
        """Return device info."""
        return self.coordinator.device_info
