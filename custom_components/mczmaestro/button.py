"""Support for MCZ buttons."""

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import CONTROLLER, COORDINATOR, DOMAIN
from .entity import MczEntity
from .maestro import MaestroController

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the MCZ button platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    controller = data[CONTROLLER]
    coordinator = data[COORDINATOR]

    async_add_entities(
        [
            MczSyncTimeButton(
                controller, coordinator, "Sync Date & Time", "sync_time", "sync_time"
            )
        ]
    )


class MczSyncTimeButton(MczEntity, ButtonEntity):
    """Push the current local date/time to the stove.

    Command format confirmed via MITM capture of the MCZ app (13.09.2026):
    ``C|SalvaDataOra|DDMMYYYYHHMM``; the stove echoes ``AA|<same string>``.
    """

    async def async_press(self) -> None:
        """Send the current time to the stove."""
        now = dt_util.now()

        def _send() -> None:
            self.controller.send_with_echo(
                f"C|SalvaDataOra|{now.strftime('%d%m%Y%H%M')}"
            )

        await self.hass.async_add_executor_job(_send)
        await self.coordinator.async_request_refresh()
