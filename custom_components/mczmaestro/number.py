"""Support for MCZ numbers."""

import logging

from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTemperature
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
    """Set up the IPX800 switches."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    controller = data[CONTROLLER]
    coordinator = data[COORDINATOR]

    entities = [
        MczNumberEntity(
            controller, coordinator, "Temperature T1", "Chronostat_T1", 1108
        ),
        MczNumberEntity(
            controller, coordinator, "Temperature T2", "Chronostat_T2", 1109
        ),
        MczNumberEntity(
            controller, coordinator, "Temperature T3", "Chronostat_T3", 1110
        ),
        # Command IDs 51/36 come from Chibald/maestrogateway's commands.py, not
        # from Aohzan's own reverse-engineering - verified against the docs but
        # not yet tested against this specific stove. Test with small changes
        # first and confirm via the read-only "Boiler Temperature"/"Power Level"
        # sensors that the applied value matches what you intended.
        MczNumberEntity(
            controller,
            coordinator,
            "Boiler Setpoint",
            "Boiler_Setpoint",
            51,
            min_value=40,
            max_value=80,
            step=1,
            unit_of_measurement=UnitOfTemperature.CELSIUS,
            device_class=NumberDeviceClass.TEMPERATURE,
            # Protocol doubles temperature values before sending (half-degree
            # resolution) - see Temperature_Setpoint in climate.py.
            write_scale=2,
        ),
        MczNumberEntity(
            controller,
            coordinator,
            "Power Level",
            "Power_Level",
            36,
            min_value=1,
            max_value=15,
            step=1,
        ),
        # Confirmed via MITM capture of the MCZ app (13.09.2026): writing
        # param 52 with value*2 sets the puffer (buffer tank) setpoint; it
        # reads back in the SetPuffer status field (now typed as temperature
        # so it is already halved). Param 52 and this readback are a genuinely
        # new discovery - not present in Aohzan/Chibald/Robbe-B.
        MczNumberEntity(
            controller,
            coordinator,
            "Puffer Setpoint",
            "SetPuffer",
            52,
            min_value=40,
            max_value=80,
            step=1,
            unit_of_measurement=UnitOfTemperature.CELSIUS,
            device_class=NumberDeviceClass.TEMPERATURE,
            write_scale=2,
        ),
    ]

    async_add_entities(entities, True)


class MczNumberEntity(MczEntity, NumberEntity):
    """Representation a Mcz number."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        controller: MaestroController,
        coordinator: DataUpdateCoordinator,
        name: str,
        command_name: str,
        command_id: int,
        min_value: float = 8,
        max_value: float = 30,
        step: float = 1,
        unit_of_measurement: str | None = UnitOfTemperature.CELSIUS,
        device_class: NumberDeviceClass | None = NumberDeviceClass.TEMPERATURE,
        write_scale: float = 1,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(controller, coordinator, name, command_name)
        self._command_id: int = command_id
        self._value: float = 0
        self._write_scale = write_scale
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._attr_device_class = device_class

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return self.coordinator.data.get(self._command_name, self._value)

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        write_value = value * self._write_scale
        if write_value == int(write_value):
            write_value = int(write_value)
        await self.hass.async_add_executor_job(
            self.controller.send,
            f"C|WriteParametri|{self._command_id!s}|{write_value!s}",
        )
        # set value in local if it's not return by the strove
        self._value = value
        await self.coordinator.async_request_refresh()
