"""Config flow to configure the MCZ Maestro integration."""

import logging
from typing import Any

import voluptuous as vol
from websocket import WebSocketException

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL

from .const import DOMAIN
from .maestro import MaestroController

_LOGGER = logging.getLogger(__name__)

BASE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="192.168.120.1"): str,
        vol.Required(CONF_PORT, default=81): int,
        vol.Required(CONF_SCAN_INTERVAL, default=30): int,
    }
)


@config_entries.HANDLERS.register(DOMAIN)
class MczConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a mczmaestro config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self) -> None:
        """Initialize class variables."""
        self.base_input: dict[str, Any] = {}

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=BASE_SCHEMA, errors=errors
            )

        entry = await self.async_set_unique_id(
            "_".join([DOMAIN, user_input[CONF_HOST], str(user_input[CONF_PORT])])
        )

        if entry:
            self._abort_if_unique_id_configured()

        try:
            # Short timeout: the stove answers within a second when reachable,
            # and the user should not stare at a spinner for a minute.
            controller = await self.hass.async_add_executor_job(
                MaestroController, user_input[CONF_HOST], user_input[CONF_PORT], 10
            )
        except (OSError, WebSocketException):
            errors["base"] = "cannot_connect"
        except Exception:
            _LOGGER.exception("Unexpected error while connecting to the stove")
            errors["base"] = "unknown"
        else:
            connected = controller.connected
            # Do not leave the test socket open on the stove.
            await self.hass.async_add_executor_job(controller.close)
            if not connected:
                errors["base"] = "cannot_connect"

        if errors:
            return self.async_show_form(
                step_id="user",
                data_schema=self.add_suggested_values_to_schema(BASE_SCHEMA, user_input),
                errors=errors,
            )

        return self.async_create_entry(
            title=f"MCZ Maestro {user_input[CONF_HOST]}:{user_input[CONF_PORT]}",
            data=user_input,
        )
