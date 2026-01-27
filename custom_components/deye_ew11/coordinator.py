"""Coordinator with enhancements but KEEPING working Modbus code!"""
from __future__ import annotations

import logging
from datetime import timedelta
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_INVERTER_TYPE,
    CONF_SLAVE_ID,
    CONF_UPDATE_INTERVAL,
    CONF_USE_CACHE,
    CONF_MAX_CACHE_AGE,
    CONF_PROTOCOL,
    CONF_BROKER_IP,
    CONF_BROKER_PORT,
    CONF_TOPIC_REQUEST,
    CONF_TOPIC_RESPONSE,
    CONF_MQTT_USERNAME,
    CONF_MQTT_PASSWORD,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_USE_CACHE,
    DEFAULT_MAX_CACHE_AGE,
    DOMAIN,
    MODBUS_TIMEOUT,
    PROTOCOL_MODBUS,
    PROTOCOL_MQTT,
)
from .modbus_client import ModbusClient
from .mqtt_client import DeyeMQTTClient

_LOGGER = logging.getLogger(__name__)


class DeyeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator with hybrid YAML support."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.protocol = entry.data.get(CONF_PROTOCOL, PROTOCOL_MODBUS)
        self.inverter_type = entry.data.get(CONF_INVERTER_TYPE, "deye_hybrid")
        self.update_interval_seconds = entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        self.use_cache = entry.data.get(CONF_USE_CACHE, DEFAULT_USE_CACHE)
        self.max_cache_age = entry.data.get(CONF_MAX_CACHE_AGE, DEFAULT_MAX_CACHE_AGE)
        
        # Cache for last known good data
        self._last_good_data: dict[str, Any] | None = None
        self._failed_updates = 0

        # Initialize protocol-specific client
        if self.protocol == PROTOCOL_MQTT:
            self.broker_ip = entry.data.get(CONF_BROKER_IP)
            broker_port = entry.data.get(CONF_BROKER_PORT, 1883)
            topic_req = entry.data.get(CONF_TOPIC_REQUEST, "deye/request")
            topic_res = entry.data.get(CONF_TOPIC_RESPONSE, "deye/response")
            mqtt_user = entry.data.get(CONF_MQTT_USERNAME, "")
            mqtt_pass = entry.data.get(CONF_MQTT_PASSWORD, "")
            
            self.client = DeyeMQTTClient(
                broker_ip=self.broker_ip,
                broker_port=broker_port,
                topic_request=topic_req,
                topic_response=topic_res,
                username=mqtt_user if mqtt_user else None,
                password=mqtt_pass if mqtt_pass else None,
            )
            self.modbus_client = None  # Not used for MQTT
            
            _LOGGER.info(
                "Coordinator init: MQTT %s:%s (Type: %s, Cache: %s)",
                self.broker_ip, broker_port, self.inverter_type, self.use_cache
            )
        else:
            # Modbus TCP
            self.host = entry.data.get(CONF_HOST, "192.168.1.103")
            self.port = entry.data.get(CONF_PORT, 502)
            self.slave_id = entry.data.get(CONF_SLAVE_ID, 1)
            
            self.modbus_client = ModbusClient(
                host=self.host,
                port=self.port,
                slave_id=self.slave_id,
                timeout=2.0,  # Increased timeout for stability
            )
            self.client = self.modbus_client  # Alias for compatibility
            
            _LOGGER.info(
                "Coordinator init: Modbus %s:%s (Type: %s, Cache: %s)",
                self.host, self.port, self.inverter_type, self.use_cache
            )
        
        # Hardcoded mode only for v1.0
        self.use_hardcoded = True

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=self.update_interval_seconds),
        )

    def _to_signed(self, val: int) -> int:
        """Convert uint16 to int16."""
        if val > 32767:
            return val - 65536
        return val

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from inverter with smart caching."""
        try:
            # Try to get fresh data
            if self.use_hardcoded:
                data = await self._update_hardcoded()
            else:
                data = await self._update_from_yaml()
            
            # If successful, cache it and reset fail counter
            if data.get("connected"):
                self._last_good_data = data.copy()
                self._failed_updates = 0
                return data
            
            # If failed but we have cache enabled and recent data
            if self.use_cache and self._last_good_data and self._failed_updates < self.max_cache_age:
                self._failed_updates += 1
                _LOGGER.warning("Using cached data (failed updates: %d/%d)", self._failed_updates, self.max_cache_age)
                cached = self._last_good_data.copy()
                cached["connected"] = True  # Show as connected but with stale data
                cached["_cache_age"] = self._failed_updates  # Internal marker
                return cached
            
            # Too many failures - show truly disconnected
            self._failed_updates += 1
            _LOGGER.error("Truly disconnected: %d failed updates", self._failed_updates)
            return {"connected": False}
            
        except Exception as err:
            _LOGGER.error("Update error: %s", err, exc_info=True)
            if self.use_cache and self._last_good_data and self._failed_updates < self.max_cache_age:
                self._failed_updates += 1
                return self._last_good_data.copy()
            return {"connected": False}

    async def _update_hardcoded(self) -> dict[str, Any]:
        """Update using hardcoded logic - supports both Modbus and MQTT!"""
        # Route to protocol-specific implementation
        if self.protocol == PROTOCOL_MQTT:
            return await self._update_mqtt()
        else:
            return await self._update_modbus()

    async def _update_mqtt(self) -> dict[str, Any]:
        """Update from MQTT broker."""
        try:
            # Get data from MQTT client
            mqtt_data = await self.client.async_get_data()
            
            if not mqtt_data or not mqtt_data.get("connected"):
                return {"connected": False}
            
            # MQTT client already returns data in the right format
            # Just ensure it has all required fields
            data = {
                "connected": True,
                "grid_voltage": mqtt_data.get("grid_voltage", 0.0),
                "grid_freq": mqtt_data.get("grid_freq", 0.0),
                "load_freq": 0.0,  # Not available via MQTT
                "grid_power": mqtt_data.get("grid_power", 0),
                "load_power": mqtt_data.get("load_power", 0),
                "battery_voltage": mqtt_data.get("battery_voltage", 0.0),
                "battery_soc": mqtt_data.get("battery_soc", 0),
                "battery_power": mqtt_data.get("battery_power", 0),
                "battery_current": mqtt_data.get("battery_current", 0.0),
                "battery_temp": mqtt_data.get("battery_temp", 0.0),
                "dc_temp": mqtt_data.get("dc_temp", 0.0),
                "ac_temp": mqtt_data.get("ac_temp", 0.0),
                "pv_power": mqtt_data.get("pv_power", 0),
                "pv1_power": mqtt_data.get("pv1_power", 0),
                "pv2_power": mqtt_data.get("pv2_power", 0),
                "pv1_voltage": 0.0,  # Not available via MQTT
                "pv1_current": 0.0,  # Not available via MQTT
                "pv2_voltage": 0.0,  # Not available via MQTT
                "pv2_current": 0.0,  # Not available via MQTT
                "inverter_current": 0.0,  # Not available via MQTT
                "day_battery_charge": mqtt_data.get("daily_battery_charge", 0.0),
                "day_battery_discharge": mqtt_data.get("daily_battery_discharge", 0.0),
                "day_grid_import": 0.0,  # Not available via MQTT
                "day_grid_export": 0.0,  # Not available via MQTT
                "day_load_energy": 0.0,  # Not available via MQTT
                "day_pv_energy": mqtt_data.get("daily_pv_production", 0.0),
            }
            
            _LOGGER.debug("📨 MQTT data: SOC=%d%%, Battery=%dW, Grid=%dW",
                         data["battery_soc"], data["battery_power"], data["grid_power"])
            
            return data
            
        except Exception as err:
            _LOGGER.error("MQTT update error: %s", err)
            return {"connected": False}

    async def _update_modbus(self) -> dict[str, Any]:
        """Update from Modbus TCP."""
        data = {
            "connected": False,
            "grid_voltage": 0.0,
            "grid_freq": 0.0,
            "load_freq": 0.0,
            "grid_power": 0,
            "load_power": 0,
            "battery_voltage": 0.0,
            "battery_soc": 0,
            "battery_power": 0,
            "battery_current": 0.0,
            "battery_temp": 0.0,
            "dc_temp": 0.0,
            "ac_temp": 0.0,
            "pv_power": 0,
            "pv1_power": 0,
            "pv2_power": 0,
            "pv1_voltage": 0.0,
            "pv1_current": 0.0,
            "pv2_voltage": 0.0,
            "pv2_current": 0.0,
            "inverter_current": 0.0,
            "day_battery_charge": 0.0,
            "day_battery_discharge": 0.0,
            "day_grid_import": 0.0,
            "day_grid_export": 0.0,
            "day_load_energy": 0.0,
            "day_pv_energy": 0.0,
        }

        try:
            # Connect
            if not await self.modbus_client.connect():
                _LOGGER.warning("Failed to connect to %s:%s", self.host, self.port)
                return data

            # Read Block 1 (60-115) - WORKING!
            regs_energy = await self.modbus_client.read_holding_registers(60, 55)
            
            # If first block failed, don't read others (connection broken)
            if not regs_energy or len(regs_energy) < 53:
                _LOGGER.warning("Failed to read energy registers (block 1), aborting")
                await self.modbus_client.disconnect()
                return data
            
            # Read Block 2 (150-196) - WORKING!
            regs_live = await self.modbus_client.read_holding_registers(150, 46)

            # Disconnect
            await self.modbus_client.disconnect()

            # Parse Block 1
            if regs_energy and len(regs_energy) >= 53:
                data["grid_freq"] = round(regs_energy[19] * 0.01, 2)
                data["day_battery_charge"] = round(regs_energy[10] * 0.1, 1)
                data["day_battery_discharge"] = round(regs_energy[11] * 0.1, 1)
                data["day_grid_import"] = round(regs_energy[16] * 0.1, 1)
                data["day_grid_export"] = round(regs_energy[17] * 0.1, 1)
                data["day_load_energy"] = round(regs_energy[24] * 0.1, 1)
                data["dc_temp"] = round((regs_energy[30] - 1000) / 10.0, 1)
                data["ac_temp"] = round((regs_energy[31] - 1000) / 10.0, 1)
                data["day_pv_energy"] = round(regs_energy[48] * 0.1, 1)
                data["pv1_voltage"] = round(regs_energy[49] * 0.1, 1)
                data["pv1_current"] = round(regs_energy[50] * 0.1, 1)
                data["pv2_voltage"] = round(regs_energy[51] * 0.1, 1)
                data["pv2_current"] = round(regs_energy[52] * 0.1, 1)

            # Parse Block 2
            if regs_live and len(regs_live) >= 44:
                data["load_freq"] = round(regs_live[43] * 0.01, 2)
                
                raw_voltage = round(regs_live[0] * 0.1, 1)
                data["grid_voltage"] = 0.0 if raw_voltage < 50 else raw_voltage
                
                data["grid_power"] = self._to_signed(regs_live[19])
                data["load_power"] = regs_live[28]
                data["inverter_current"] = round(self._to_signed(regs_live[14]) * 0.01, 2)
                
                # Generator (Register 166 = 0xA6)
                data["gen_power"] = self._to_signed(regs_live[16])
                
                data["battery_temp"] = round((regs_live[32] - 1000) / 10.0, 1)
                data["battery_voltage"] = regs_live[33] * 0.01
                data["battery_soc"] = regs_live[34]
                data["battery_power"] = self._to_signed(regs_live[40])
                data["battery_current"] = round(self._to_signed(regs_live[41]) * 0.01, 2)
                
                data["pv1_power"] = regs_live[36]
                data["pv2_power"] = regs_live[37]
                data["pv_power"] = data["pv1_power"] + data["pv2_power"]

                # Enhanced validation to prevent garbage values
                is_valid = True
                validation_errors = []
                
                # Battery SOC: 0-100% (allow 105% for small overcharge)
                if data["battery_soc"] < 0 or data["battery_soc"] > 105:
                    is_valid = False
                    validation_errors.append(f"SOC={data['battery_soc']}%")
                
                # Battery Voltage: 40-60V typical for 48V systems
                if data["battery_voltage"] < 35 or data["battery_voltage"] > 65:
                    is_valid = False
                    validation_errors.append(f"Voltage={data['battery_voltage']}V")
                
                # Battery Temperature: -20 to +60°C realistic range
                if data["battery_temp"] < -25 or data["battery_temp"] > 70:
                    is_valid = False
                    validation_errors.append(f"Temp={data['battery_temp']}°C")
                
                # Grid Voltage: 180-260V for 230V systems (excluding 0)
                if data["grid_voltage"] > 0 and (data["grid_voltage"] < 170 or data["grid_voltage"] > 270):
                    is_valid = False
                    validation_errors.append(f"GridV={data['grid_voltage']}V")
                
                # Power values: -50kW to +50kW reasonable limits
                for key in ["battery_power", "grid_power", "load_power", "pv_power"]:
                    if abs(data[key]) > 50000:
                        is_valid = False
                        validation_errors.append(f"{key}={data[key]}W")

                if is_valid:
                    data["connected"] = True
                    _LOGGER.info("✅ Data OK: SOC=%d%%, Bat=%.2fV, PV=%dW, Grid=%dW, Load=%dW", 
                                data["battery_soc"], data["battery_voltage"], 
                                data["pv_power"], data["grid_power"], data["load_power"])
                else:
                    _LOGGER.error("❌ Invalid data detected: %s - Using cached data if available", 
                                 ", ".join(validation_errors))
                    # Return last good data if available, otherwise disconnected
                    if self._last_good_data:
                        _LOGGER.warning("Returning last valid cached data instead of garbage")
                        return self._last_good_data.copy()
                    else:
                        _LOGGER.warning("No cache available, returning disconnected")
                        return {"connected": False}

            return data

        except Exception as err:
            _LOGGER.error("Error updating: %s", err, exc_info=True)
            try:
                if self.modbus_client:
                    await self.modbus_client.disconnect()
            except:
                pass
            return {"connected": False}

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        _LOGGER.info("Shutting down coordinator")
        
        # Disconnect protocol-specific client
        if self.protocol == PROTOCOL_MQTT:
            if hasattr(self, 'client') and self.client:
                await self.client.disconnect()
        else:
            if self.modbus_client:
                await self.modbus_client.disconnect()
    
    async def async_config_entry_updated(self) -> None:
        """Handle config updates."""
        new_interval = self.entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        if new_interval != self.update_interval_seconds:
            _LOGGER.info("Update interval changed: %ds -> %ds", self.update_interval_seconds, new_interval)
            self.update_interval_seconds = new_interval
            self.update_interval = timedelta(seconds=new_interval)

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        # Use broker_ip for MQTT, host for Modbus
        if self.protocol == PROTOCOL_MQTT:
            config_url = f"http://{self.broker_ip}"
        else:
            config_url = f"http://{self.host}"
        
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": self.entry.title,
            "manufacturer": "Deye",
            "model": "Hybrid Inverter (EW11)",
            "sw_version": "1.0.1",
            "configuration_url": config_url,
        }
