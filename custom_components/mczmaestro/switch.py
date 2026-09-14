"""Support for the MCZ switches."""

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONTROLLER, COORDINATOR, DOMAIN
from .entity import MczEntity
from .maestro import MaestroController

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the MCZ platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    controller = data[CONTROLLER]
    coordinator = data[COORDINATOR]

    entities = [
        MczSwitchEntity(
            controller, coordinator, "Eco Mode", "Eco_Mode", 41, "eco_mode"
        ),
        MczSwitchEntity(
            controller, coordinator, "Silent Mode", "Silent_Mode", 45, "silent_mode"
        ),
        MczSwitchEntity(
            controller, coordinator, "Active Mode", "Active_Mode", 35, "active_mode"
        ),
        MczSwitchEntity(
            controller,
            coordinator,
            "Dynamic Mode",
            "Control_Mode",
            40,
            "dynamic_mode",
        ),
        MczSwitchEntity(
            controller, coordinator, "Chrono Mode", "Chronostat", 1111, "chrono_mode"
        ),
        # Confirmed via MITM capture of the MCZ app (13.09.2026): writing param
        # 58 with 1/0 switches summer/winter mode; it reads back in the "Mode"
        # status field (1 = summer, 0 = winter). Genuinely new discovery.
        MczSwitchEntity(
            controller, coordinator, "Summer Mode", "Mode", 58, "summer_mode"
        ),
    ]
    if entities:
        async_add_entities(entities)


class MczSwitchEntity(MczEntity, SwitchEntity):
    """Representation of a MCZ switch."""

    def __init__(
        self,
        controller: MaestroController,
        coordinator: DataUpdateCoordinator,
        name: str,
        command_name: str,
        command_id: int,
        translation_key: str | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(controller, coordinator, name, command_name, translation_key)
        self._command_id: int = command_id

    @property
    def is_on(self) -> bool:
        """Return the state."""
        return int(self.coordinator.data[self._command_name]) == 1

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        await self.hass.async_add_executor_job(
            self.controller.send, f"C|WriteParametri|{self._command_id!s}|1"
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        await self.hass.async_add_executor_job(
            self.controller.send, f"C|WriteParametri|{self._command_id!s}|0"
        )
        await self.coordinator.async_request_refresh()
