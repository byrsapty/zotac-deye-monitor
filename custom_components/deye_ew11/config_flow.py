"""Config flow with ALL settings in options."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_BATTERY_CAPACITY,
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
    DEFAULT_BATTERY_CAPACITY,
    DEFAULT_INVERTER_TYPE,
    DEFAULT_PORT,
    DEFAULT_SLAVE_ID,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_USE_CACHE,
    DEFAULT_MAX_CACHE_AGE,
    DEFAULT_PROTOCOL,
    DEFAULT_BROKER_PORT,
    DEFAULT_TOPIC_REQUEST,
    DEFAULT_TOPIC_RESPONSE,
    DOMAIN,
    INVERTER_TYPES,
    PROTOCOL_MODBUS,
    PROTOCOL_MQTT,
)

_LOGGER = logging.getLogger(__name__)


class DeyeEW11ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Deye EW11."""

    VERSION = 1

    def __init__(self):
        """Initialize config flow."""
        self._protocol = None
        self._config = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle protocol selection."""
        if user_input is not None:
            self._protocol = user_input[CONF_PROTOCOL]
            
            # Move to protocol-specific step
            if self._protocol == PROTOCOL_MODBUS:
                return await self.async_step_modbus()
            else:
                return await self.async_step_mqtt()

        # Show protocol selector
        data_schema = vol.Schema({
            vol.Required(CONF_PROTOCOL, default=DEFAULT_PROTOCOL): vol.In({
                PROTOCOL_MODBUS: "Modbus TCP",
                PROTOCOL_MQTT: "MQTT (via Mosquitto)",
            }),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )

    async def async_step_modbus(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle Modbus TCP configuration."""
        if user_input is not None:
            self._config.update(user_input)
            self._config[CONF_PROTOCOL] = PROTOCOL_MODBUS
            
            await self.async_set_unique_id(
                f"{user_input[CONF_HOST]}_{user_input[CONF_SLAVE_ID]}"
            )
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input.get(CONF_NAME, "Deye Inverter"),
                data=self._config,
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="Deye Inverter"): str,
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): int,
                vol.Required(
                    CONF_INVERTER_TYPE, default=DEFAULT_INVERTER_TYPE
                ): vol.In(INVERTER_TYPES),
                vol.Optional(
                    CONF_BATTERY_CAPACITY, default=DEFAULT_BATTERY_CAPACITY
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                ): int,
                vol.Optional(
                    CONF_USE_CACHE, default=DEFAULT_USE_CACHE
                ): bool,
                vol.Optional(
                    CONF_MAX_CACHE_AGE, default=DEFAULT_MAX_CACHE_AGE
                ): int,
            }
        )

        return self.async_show_form(
            step_id="modbus",
            data_schema=data_schema,
        )

    async def async_step_mqtt(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle MQTT configuration."""
        if user_input is not None:
            self._config.update(user_input)
            self._config[CONF_PROTOCOL] = PROTOCOL_MQTT
            
            await self.async_set_unique_id(
                f"mqtt_{user_input[CONF_BROKER_IP]}_{user_input.get(CONF_BROKER_PORT, 1883)}"
            )
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input.get(CONF_NAME, "Deye Inverter (MQTT)"),
                data=self._config,
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="Deye Inverter (MQTT)"): str,
                vol.Required(CONF_BROKER_IP): str,
                vol.Required(CONF_BROKER_PORT, default=DEFAULT_BROKER_PORT): int,
                vol.Optional(CONF_MQTT_USERNAME, default=""): str,
                vol.Optional(CONF_MQTT_PASSWORD, default=""): str,
                vol.Optional(CONF_TOPIC_REQUEST, default=DEFAULT_TOPIC_REQUEST): str,
                vol.Optional(CONF_TOPIC_RESPONSE, default=DEFAULT_TOPIC_RESPONSE): str,
                vol.Required(
                    CONF_INVERTER_TYPE, default=DEFAULT_INVERTER_TYPE
                ): vol.In(INVERTER_TYPES),
                vol.Optional(
                    CONF_BATTERY_CAPACITY, default=DEFAULT_BATTERY_CAPACITY
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                ): int,
            }
        )


        return self.async_show_form(
            step_id="mqtt",
            data_schema=data_schema,
        )


    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options - ALL settings editable."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        pass

    async def async_step_init(self, user_input=None):
        """Manage ALL options."""
        if user_input is not None:
            # Get current protocol
            protocol = self.config_entry.data.get(CONF_PROTOCOL, PROTOCOL_MODBUS)
            
            # Build new data based on protocol
            if protocol == PROTOCOL_MQTT:
                new_data = {
                    CONF_PROTOCOL: PROTOCOL_MQTT,
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_BROKER_IP: user_input[CONF_BROKER_IP],
                    CONF_BROKER_PORT: user_input[CONF_BROKER_PORT],
                    CONF_MQTT_USERNAME: user_input.get(CONF_MQTT_USERNAME, ""),
                    CONF_MQTT_PASSWORD: user_input.get(CONF_MQTT_PASSWORD, ""),
                    CONF_TOPIC_REQUEST: user_input.get(CONF_TOPIC_REQUEST, DEFAULT_TOPIC_REQUEST),
                    CONF_TOPIC_RESPONSE: user_input.get(CONF_TOPIC_RESPONSE, DEFAULT_TOPIC_RESPONSE),
                    CONF_INVERTER_TYPE: user_input[CONF_INVERTER_TYPE],
                    CONF_BATTERY_CAPACITY: user_input[CONF_BATTERY_CAPACITY],
                    CONF_UPDATE_INTERVAL: user_input[CONF_UPDATE_INTERVAL],
                }
            else:
                new_data = {
                    CONF_PROTOCOL: PROTOCOL_MODBUS,
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_PORT: user_input[CONF_PORT],
                    CONF_SLAVE_ID: user_input[CONF_SLAVE_ID],
                    CONF_INVERTER_TYPE: user_input[CONF_INVERTER_TYPE],
                    CONF_BATTERY_CAPACITY: user_input[CONF_BATTERY_CAPACITY],
                    CONF_UPDATE_INTERVAL: user_input[CONF_UPDATE_INTERVAL],
                    CONF_USE_CACHE: user_input.get(CONF_USE_CACHE, DEFAULT_USE_CACHE),
                    CONF_MAX_CACHE_AGE: user_input.get(CONF_MAX_CACHE_AGE, DEFAULT_MAX_CACHE_AGE),
                }
            
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=new_data, title=new_data[CONF_NAME]
            )
            
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            
            return self.async_create_entry(title="", data={})

        # Current values
        data = self.config_entry.data
        protocol = data.get(CONF_PROTOCOL, PROTOCOL_MODBUS)
        
        # Build schema based on protocol
        if protocol == PROTOCOL_MQTT:
            schema = vol.Schema({
                vol.Required(
                    CONF_NAME, default=data.get(CONF_NAME, "Deye Inverter (MQTT)")
                ): str,
                vol.Required(
                    CONF_BROKER_IP, default=data.get(CONF_BROKER_IP, "127.0.0.1")
                ): str,
                vol.Required(
                    CONF_BROKER_PORT, default=data.get(CONF_BROKER_PORT, DEFAULT_BROKER_PORT)
                ): int,
                vol.Optional(
                    CONF_MQTT_USERNAME, default=data.get(CONF_MQTT_USERNAME, "")
                ): str,
                vol.Optional(
                    CONF_MQTT_PASSWORD, default=data.get(CONF_MQTT_PASSWORD, "")
                ): str,
                vol.Optional(
                    CONF_TOPIC_REQUEST, default=data.get(CONF_TOPIC_REQUEST, DEFAULT_TOPIC_REQUEST)
                ): str,
                vol.Optional(
                    CONF_TOPIC_RESPONSE, default=data.get(CONF_TOPIC_RESPONSE, DEFAULT_TOPIC_RESPONSE)
                ): str,
                vol.Required(
                    CONF_INVERTER_TYPE, default=data.get(CONF_INVERTER_TYPE, DEFAULT_INVERTER_TYPE)
                ): vol.In(INVERTER_TYPES),
                vol.Required(
                    CONF_BATTERY_CAPACITY, default=data.get(CONF_BATTERY_CAPACITY, DEFAULT_BATTERY_CAPACITY)
                ): vol.Coerce(float),
                vol.Required(
                    CONF_UPDATE_INTERVAL, default=data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
                ): int,
            })
        else:
            schema = vol.Schema({
                vol.Required(
                    CONF_NAME, default=data.get(CONF_NAME, "Deye Inverter")
                ): str,
                vol.Required(
                    CONF_HOST, default=data.get(CONF_HOST, "192.168.1.103")
                ): str,
                vol.Required(
                    CONF_PORT, default=data.get(CONF_PORT, DEFAULT_PORT)
                ): int,
                vol.Required(
                    CONF_SLAVE_ID, default=data.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID)
                ): int,
                vol.Required(
                    CONF_INVERTER_TYPE, default=data.get(CONF_INVERTER_TYPE, DEFAULT_INVERTER_TYPE)
                ): vol.In(INVERTER_TYPES),
                vol.Required(
                    CONF_BATTERY_CAPACITY, default=data.get(CONF_BATTERY_CAPACITY, DEFAULT_BATTERY_CAPACITY)
                ): vol.Coerce(float),
                vol.Required(
                    CONF_UPDATE_INTERVAL, default=data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
                ): int,
                vol.Required(
                    CONF_USE_CACHE, default=data.get(CONF_USE_CACHE, DEFAULT_USE_CACHE)
                ): bool,
                vol.Required(
                    CONF_MAX_CACHE_AGE, default=data.get(CONF_MAX_CACHE_AGE, DEFAULT_MAX_CACHE_AGE)
                ): int,
            })
        
        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )
