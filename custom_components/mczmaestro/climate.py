"""Support for the MCZ climate."""

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONTROLLER, COORDINATOR, DOMAIN
from .entity import MczEntity
from .maestro import get_maestro_power_state

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

    entities = []

    entities.append(
        MczClimateEntity(controller, coordinator, "Stove", "stove"),
    )
    if entities:
        async_add_entities(entities)


class MczClimateEntity(MczEntity, ClimateEntity):
    """Representation of a MCZ climate."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.AUTO, HVACMode.OFF]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_target_temperature_step = 0.5

    @property
    def current_temperature(self) -> float:
        """Return the current temperature."""
        return float(self.coordinator.data["Ambient_Temperature"])

    @property
    def target_temperature(self) -> float:
        """Return the temperature we try to reach."""
        return float(self.coordinator.data["Temperature_Setpoint"])

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current running hvac operation if supported."""
        # Derived from the real stove phase. Active_Mode is MCZ's "Active"
        # combustion feature, not a heating indicator, and Extinguish/Cooling
        # count as "powered" in MAESTRO_STOVESTATE although nothing burns.
        state = int(self.coordinator.data["Stove_State"])
        if 1 <= state <= 15 or state in (31, 42, 43):
            return HVACAction.HEATING
        if state in (40, 41, 45, 46):
            return HVACAction.IDLE
        return HVACAction.OFF

    @property
    def hvac_mode(self) -> HVACMode:
        """Return hvac operation ie. heat, cool mode."""
        if get_maestro_power_state(int(self.coordinator.data["Stove_State"])) == 0:
            return HVACMode.OFF
        if int(self.coordinator.data["Control_Mode"]) == 1:
            return HVACMode.AUTO
        return HVACMode.HEAT

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        value = float(kwargs[ATTR_TEMPERATURE]) * 2
        await self.hass.async_add_executor_job(
            self.controller.send, f"C|WriteParametri|42|{value}"
        )
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""

        def _send() -> None:
            # Values arrive from the protocol parser as strings, so a bare
            # "0" == 0 never matched and the power-on command was never sent.
            # Use the same power-state lookup as hvac_mode/hvac_action above:
            # Standby (46) and Auto Eco (45) also count as off, so comparing
            # against 0 alone would still miss those states.
            # Cooling (41) counts as powered, but the stove stays there until
            # the flue drops below ~60 °C, which a hot boiler with the pump
            # stopped can prevent for hours. Power-on restarts it, exactly
            # like the panel's power key.
            state = int(self.coordinator.data["Stove_State"])
            if hvac_mode != HVACMode.OFF and (
                not get_maestro_power_state(state) or state == 41
            ):
                self.controller.send("C|WriteParametri|34|1")
            if hvac_mode == HVACMode.AUTO:
                self.controller.send("C|WriteParametri|40|1")
            elif hvac_mode == HVACMode.HEAT:
                self.controller.send("C|WriteParametri|40|0")
            elif hvac_mode == HVACMode.OFF:
                # turn off eco and dynamic mode and shutdown
                self.controller.send("C|WriteParametri|41|0")
                self.controller.send("C|WriteParametri|1111|0")
                self.controller.send("C|WriteParametri|34|40")

        await self.hass.async_add_executor_job(_send)
        await self.coordinator.async_request_refresh()
