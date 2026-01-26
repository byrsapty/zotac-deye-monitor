"""Native Modbus TCP client - EXACTLY matching user's get_deye.py."""
from __future__ import annotations

import asyncio
import logging
import socket
import struct
from typing import List

_LOGGER = logging.getLogger(__name__)


class ModbusClient:
    """Simple Modbus TCP client - EXACT copy of user's working code."""

    def __init__(
        self,
        host: str,
        port: int = 502,
        slave_id: int = 1,
        timeout: float = 2.0,  # Increased for WiFi stability
    ) -> None:
        """Initialize the Modbus client."""
        self.host = host
        self.port = port
        self.slave_id = slave_id
        self.timeout = timeout
        self._socket = None
        self.is_connected = False

    def _connect_sync(self) -> bool:
        """Connect to the Modbus device (synchronous)."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(self.timeout)  # User's 1.2s timeout
            self._socket.connect((self.host, self.port))
            self.is_connected = True
            _LOGGER.debug("Connected to Modbus at %s:%s", self.host, self.port)
            return True
        except Exception as err:
            _LOGGER.error("Connection error to %s:%s - %s", self.host, self.port, err)
            self.is_connected = False
            if self._socket:
                try:
                    self._socket.close()
                except:
                    pass
                self._socket = None
            return False

    async def connect(self) -> bool:
        """Connect to the Modbus device (async wrapper)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._connect_sync)

    async def disconnect(self) -> None:
        """Disconnect from the Modbus device."""
        if self._socket:
            try:
                self._socket.close()
                self.is_connected = False
            except Exception as err:
                _LOGGER.error("Disconnect error: %s", err)
            finally:
                self._socket = None

    def _read_registers_sync(self, address: int, count: int) -> List[int] | None:
        """Read holding registers - EXACT copy of user's read_block function."""
        if not self._socket:
            _LOGGER.warning("Not connected")
            return None

        try:
            # Build Modbus RTU request - EXACTLY like user's code
            pdu = struct.pack(">B B H H", self.slave_id, 3, address, count)
            
            # Calculate CRC16 - EXACTLY like user's code
            crc = 0xFFFF
            for byte in pdu:
                crc ^= byte
                for _ in range(8):
                    if crc & 0x0001:
                        crc = (crc >> 1) ^ 0xA001
                    else:
                        crc >>= 1
            
            # Send request
            request = pdu + struct.pack("<H", crc)
            self._socket.sendall(request)
            
            # Receive response header (3 bytes)
            header = self._socket.recv(3)
            if len(header) < 3:
                _LOGGER.error("Invalid response header")
                return None
            
            _, _, byte_count = struct.unpack("BBB", header)
            
            # Receive data + CRC (SINGLE recv like user's code! NO LOOP!)
            raw_data = self._socket.recv(byte_count + 2)
            
            # Parse registers
            registers = []
            for i in range(0, byte_count, 2):
                reg_value = struct.unpack(">H", raw_data[i:i+2])[0]
                registers.append(reg_value)
            
            return registers

        except socket.timeout:
            _LOGGER.error("Timeout reading registers at %d", address)
            return None
        except Exception as err:
            _LOGGER.error("Error reading registers at %d: %s", address, err)
            return None

    async def read_holding_registers(
        self, address: int, count: int
    ) -> List[int] | None:
        """Read holding registers with retry logic (async wrapper)."""
        max_retries = 2
        retry_delay = 0.3  # seconds
        
        for attempt in range(max_retries + 1):
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._read_registers_sync, address, count)
            
            if result is not None:
                if attempt > 0:
                    _LOGGER.info(" Retry %d successful for register %d", attempt, address)
                return result
            
            # If failed and not last attempt - retry with backoff
            if attempt < max_retries:
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff: 0.3s, 0.6s
                _LOGGER.warning(" Retry %d/%d for register %d after %.1fs", 
                               attempt + 1, max_retries, address, wait_time)
                await asyncio.sleep(wait_time)
        
        # All retries failed
        _LOGGER.error(" All %d retries failed for register %d", max_retries + 1, address)
        return None

