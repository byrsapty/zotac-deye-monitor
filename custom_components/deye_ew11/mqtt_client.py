"""MQTT Client for Deye EW11 - Request-Response Modbus Bridge."""
import asyncio
import logging
import struct
from typing import Any, Dict, Optional

# Dynamic import of paho-mqtt (optional dependency)
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    mqtt = None

_LOGGER = logging.getLogger(__name__)


class DeyeMQTTClient:
    """MQTT client for Deye inverter using EW11 as Modbus bridge."""

    def __init__(
        self,
        broker_ip: str,
        broker_port: int = 1883,
        topic_request: str = "deye/request",
        topic_response: str = "deye/response",
        username: str = None,
        password: str = None,
    ):
        """Initialize MQTT client."""
        if not MQTT_AVAILABLE:
            raise ImportError(
                "paho-mqtt is required for MQTT protocol. "
                "Install it with: pip install paho-mqtt>=2.0.0"
            )
        
        self.broker_ip = broker_ip
        self.broker_port = broker_port
        self.topic_request = topic_request
        self.topic_response = topic_response
        self.username = username
        self.password = password
        
        self._client: Optional[mqtt.Client] = None
        self._data: Dict[str, Any] = {}
        self._response_event = asyncio.Event()
        self._response_data: Optional[bytes] = None
        self._is_connected = False
        self._lock = asyncio.Lock()

    @staticmethod
    def _compute_crc(data: bytes) -> bytes:
        """Compute Modbus CRC16."""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc = crc >> 1
        return struct.pack('<H', crc)

    @staticmethod
    def _build_request(start: int, count: int) -> bytes:
        """Build Modbus request packet."""
        req = struct.pack('>BBHH', 1, 3, start, count)
        req += DeyeMQTTClient._compute_crc(req)
        return req

    def _on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection."""
        if rc == 0:
            _LOGGER.info("✅ MQTT: Connected to broker at %s:%s", self.broker_ip, self.broker_port)
            self._is_connected = True
            client.subscribe(self.topic_response)
        else:
            _LOGGER.error("❌ MQTT: Connection failed with code %s", rc)
            self._is_connected = False

    def _on_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection."""
        _LOGGER.warning("⚠️ MQTT: Disconnected (code %s)", rc)
        self._is_connected = False

    def _on_message(self, client, userdata, msg):
        """Handle MQTT message (response from EW11)."""
        _LOGGER.debug("📩 MQTT: Received message on topic '%s' (%d bytes)", msg.topic, len(msg.payload))
        self._response_data = msg.payload
        self._response_event.set()

    async def connect(self) -> bool:
        """Connect to MQTT broker."""
        try:
            # Create client only once (first time or after disconnect)
            if self._client is None:
                self._client = mqtt.Client()
                self._client.on_connect = self._on_connect
                self._client.on_disconnect = self._on_disconnect
                self._client.on_message = self._on_message
                
                # Set credentials if provided
                if self.username and self.password:
                    self._client.username_pw_set(self.username, self.password)
                    _LOGGER.debug("MQTT: Using authentication (user: %s)", self.username)

            # Run connection in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                lambda: self._client.connect(self.broker_ip, self.broker_port, 60)
            )
            
            # Start MQTT loop in background (only if not already running)
            if not self._client._thread:
                self._client.loop_start()
            
            # Wait for connection (max 5 seconds)
            for _ in range(50):
                if self._is_connected:
                    return True
                await asyncio.sleep(0.1)
            
            _LOGGER.error("MQTT connection timeout")
            return False

        except Exception as err:
            _LOGGER.error("MQTT connection error: %s", err)
            return False

    async def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._is_connected = False
            _LOGGER.info("MQTT: Disconnected")

    async def _request_block(self, start: int, count: int, block_name: str) -> Optional[bytes]:
        """Request a block of registers via MQTT."""
        async with self._lock:
            try:
                # Build and send request
                request = self._build_request(start, count)
                _LOGGER.debug("📤 MQTT: Requesting %s (Reg %d-%d)", block_name, start, start + count - 1)
                
                self._response_event.clear()
                self._response_data = None
                
                self._client.publish(self.topic_request, request)
                
                # Wait for response (max 10 seconds)
                try:
                    await asyncio.wait_for(self._response_event.wait(), timeout=10.0)
                except asyncio.TimeoutError:
                    _LOGGER.error("❌ MQTT: Timeout waiting for %s", block_name)
                    return None
                
                if self._response_data:
                    _LOGGER.debug("📩 MQTT: Received %s (%d bytes)", block_name, len(self._response_data))
                    return self._response_data
                
                return None

            except Exception as err:
                _LOGGER.error("MQTT request error for %s: %s", block_name, err)
                return None

    @staticmethod
    def _parse_block1(raw: bytes) -> Dict[str, Any]:
        """Parse energy and temperature block (Reg 60-115)."""
        try:
            data_bytes = raw[3 : 3 + (55 * 2)]
            values = struct.unpack(f'>55H', data_bytes)
            
            return {
                "daily_battery_charge": round(values[10] * 0.1, 1),      # Reg 70
                "daily_battery_discharge": round(values[11] * 0.1, 1),   # Reg 71
                "day_grid_import": round(values[16] * 0.1, 1),           # Reg 76
                "day_grid_export": round(values[17] * 0.1, 1),           # Reg 77
                "grid_freq": round(values[19] * 0.01, 2),                # Reg 79
                "day_load_energy": round(values[24] * 0.1, 1),           # Reg 84
                "dc_temp": round((values[30] - 1000) * 0.1, 1),          # Reg 90
                "ac_temp": round((values[31] - 1000) * 0.1, 1),          # Reg 91
                "total_pv_production": round(values[36] * 0.1, 1),       # Reg 96
                "daily_pv_production": round(values[48] * 0.1, 1),       # Reg 108
                "pv1_voltage": round(values[49] * 0.1, 1),               # Reg 109
                "pv1_current": round(values[50] * 0.1, 1),               # Reg 110
                "pv2_voltage": round(values[51] * 0.1, 1),               # Reg 111
                "pv2_current": round(values[52] * 0.1, 1),               # Reg 112
            }
        except Exception as err:
            _LOGGER.error("Error parsing block 1: %s", err)
            return {}

    @staticmethod
    def _parse_block2(raw: bytes) -> Dict[str, Any]:
        """Parse live data block (Reg 150-196)."""
        try:
            data_bytes = raw[3 : 3 + (47 * 2)]
            values = struct.unpack(f'>47H', data_bytes)
            
            # Helper for signed values
            def s(val): return val - 65536 if val > 32767 else val
            
            # Filter noise < 50V for grid voltage
            grid_volts = round(values[0] * 0.1, 1)
            if grid_volts < 50.0:
                grid_volts = 0.0

            return {
                "grid_voltage": grid_volts,                              # Reg 150
                "load_voltage": round(values[4] * 0.1, 1),               # Reg 154
                "inverter_current": round(s(values[14]) * 0.01, 2),       # Reg 164
                "gen_power": s(values[16]),                              # Reg 166 (Generator)
                "grid_power": s(values[19]),                             # Reg 169
                "load_power": s(values[28]),                             # Reg 178
                "battery_temp": round((values[32] - 1000) * 0.1, 1),     # Reg 182
                "battery_voltage": round(values[33] * 0.01, 2),          # Reg 183
                "battery_soc": values[34],                               # Reg 184
                "pv1_power": s(values[36]),                              # Reg 186
                "pv2_power": s(values[37]),                              # Reg 187
                "battery_power": s(values[40]),                          # Reg 190
                "battery_current": round(s(values[41]) * 0.01, 2),       # Reg 191
                "load_freq": round(values[43] * 0.01, 2),                # Reg 193
            }
        except Exception as err:
            _LOGGER.error("Error parsing block 2: %s", err)
            return {}

    async def async_get_data(self) -> Dict[str, Any]:
        """Fetch all data from inverter via MQTT."""
        if not self._is_connected:
            _LOGGER.warning("MQTT not connected, attempting reconnect...")
            if not await self.connect():
                return {"connected": False}

        try:
            # Request Block 1: Energy and Temperatures
            block1_raw = await self._request_block(60, 55, "Block 1 (Energy)")
            if not block1_raw:
                return {"connected": False}
            
            # Small delay between requests
            await asyncio.sleep(0.5)
            
            # Request Block 2: Live Data
            block2_raw = await self._request_block(150, 47, "Block 2 (Live Data)")
            if not block2_raw:
                return {"connected": False}
            
            # Parse both blocks
            data1 = self._parse_block1(block1_raw)
            data2 = self._parse_block2(block2_raw)
            
            # Combine data
            combined = {
                "connected": True,
                **data1,
                **data2,
                "pv_power": data2.get("pv1_power", 0) + data2.get("pv2_power", 0),
            }
            
            self._data = combined
            
            _LOGGER.debug(
                "📊 MQTT data: SOC=%d%%, Battery=%dW, Grid=%dW, Load=%dW",
                combined.get("battery_soc", 0),
                combined.get("battery_power", 0),
                combined.get("grid_power", 0),
                combined.get("load_power", 0),
            )
            
            return combined

        except Exception as err:
            _LOGGER.error("Error fetching MQTT data: %s", err)
            return {"connected": False}

    @property
    def is_connected(self) -> bool:
        """Return connection status."""
        return self._is_connected
