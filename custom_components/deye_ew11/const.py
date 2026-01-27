"""Constants for the Deye EW11 integration."""

from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT

DOMAIN = "deye_ew11"

# Configuration keys
CONF_SLAVE_ID = "slave_id"
CONF_INVERTER_TYPE = "inverter_type"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_BATTERY_CAPACITY = "battery_capacity"
CONF_USE_CACHE = "use_cache"  # NEW: Cache last data on temporary failures
CONF_MAX_CACHE_AGE = "max_cache_age"  # NEW: Max failed attempts before showing Disconnected

# MQTT Configuration
CONF_PROTOCOL = "protocol"
CONF_BROKER_IP = "broker_ip"
CONF_BROKER_PORT = "broker_port"
CONF_TOPIC_REQUEST = "topic_request"
CONF_TOPIC_RESPONSE = "topic_response"

# Protocol options
PROTOCOL_MODBUS = "modbus"
PROTOCOL_MQTT = "mqtt"

# Default values
DEFAULT_NAME = "Deye Inverter"
DEFAULT_PORT = 502
DEFAULT_SLAVE_ID = 1
DEFAULT_INVERTER_TYPE = "deye_hybrid"
DEFAULT_UPDATE_INTERVAL = 5  # seconds
DEFAULT_BATTERY_CAPACITY = 10.24  # kWh
DEFAULT_USE_CACHE = True  # NEW: Default ON - use cached data
DEFAULT_MAX_CACHE_AGE = 3  # NEW: Show Disconnected after 3 failed updates

# MQTT defaults
DEFAULT_PROTOCOL = PROTOCOL_MODBUS
DEFAULT_BROKER_PORT = 1883
DEFAULT_TOPIC_REQUEST = "deye/request"
DEFAULT_TOPIC_RESPONSE = "deye/response"

# Timeouts
MODBUS_TIMEOUT = 3  # seconds (not used, client uses 1.2)

# Directories
INVERTER_DEFINITIONS_DIR = "inverter_definitions"

# Supported inverter types
# Models with hardcoded support (proven working)
INVERTER_TYPES_HARDCODED = {
    "deye_hybrid": "Deye Hybrid (SG01/04/05LP1) ✅",
}

# Models that require YAML definitions
INVERTER_TYPES_YAML = {
    "deye_string": "Deye String Inverter (YAML)",
    "deye_micro": "Deye Microinverter (YAML)",
    "deye_sg04lp3": "Deye SG04LP3 3-Phase (YAML)",
}

# Combined list for UI
INVERTER_TYPES = {**INVERTER_TYPES_HARDCODED, **INVERTER_TYPES_YAML}
