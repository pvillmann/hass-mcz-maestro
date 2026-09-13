"""Support for the MCZ sensors."""

from collections.abc import Mapping
import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONTROLLER, COORDINATOR, DOMAIN
from .entity import MczEntity
from .maestro import MaestroController, get_maestro_state_description

_LOGGER = logging.getLogger(__name__)

# Fields already exposed elsewhere (climate/switch/number) - not duplicated here.
_ALREADY_EXPOSED = {
    "Temperature_Setpoint",  # climate target_temperature
    "Eco_Mode",  # switch
    "Silent_Mode",  # switch
    "Active_Mode",  # switch
    "Control_Mode",  # switch
    "Chronostat",  # switch
    "Chronostat_T1",  # number
    "Chronostat_T2",  # number
    "Chronostat_T3",  # number
    "Boiler_Setpoint",  # number
    "Power_Level",  # number
    "SetPuffer",  # number (Puffer Setpoint)
    "Mode",  # switch (Summer Mode)
    "Stove_State",  # covered by the "State" sensor's own value/attributes
    "Messagetype",  # protocol plumbing, not a real measurement
    "Unknown",  # protocol plumbing
}

# name, command_name - temperature fields (halved-hex in the protocol, already converted to
# floats by process_infostring)
_TEMPERATURE_SENSORS = [
    ("Puffer Temperature", "Puffer_Temperature"),
    ("Boiler Temperature", "Boiler_Temperature"),
    ("NTC3 Temperature", "NTC3_Temperature"),
    ("Return Temperature", "Return_Temperature"),
    ("Motherboard Temperature", "Temperature_Motherboard"),
    ("WiFi Sonde Temperature 1", "WifiSondeTemperature1"),
    ("WiFi Sonde Temperature 2", "WifiSondeTemperature2"),
    ("WiFi Sonde Temperature 3", "WifiSondeTemperature3"),
]

# name, command_name - headline operational values, visible on the main entity list
_MAIN_SENSORS = [
    ("Hours To Service", "Hours_To_Service"),
    ("Minutes To Switch Off", "Minutes_To_Switch_Off"),
    ("Number Of Ignitions", "Number_Of_Ignitions"),
    ("Total Operating Hours", "Total_Operating_Hours"),
    ("Hours Power 1", "Hours_Of_Operation_In_Power1"),
    ("Hours Power 2", "Hours_Of_Operation_In_Power2"),
    ("Hours Power 3", "Hours_Of_Operation_In_Power3"),
    ("Hours Power 4", "Hours_Of_Operation_In_Power4"),
    ("Hours Power 5", "Hours_Of_Operation_In_Power5"),
    ("Fume Temperature", "Fume_Temperature"),
]

# name, command_name - low-level/technical values, tucked under "Diagnostic"
_DIAGNOSTIC_SENSORS = [
    ("Fan State", "Fan_State"),
    ("Ducted Fan 1", "DuctedFan1"),
    ("Ducted Fan 2", "DuctedFan2"),
    ("Candle Condition", "Candle_Condition"),
    ("Active Set", "ACTIVE_Set"),
    ("Fume Fan RPM", "RPM_Fam_Fume"),
    ("Worm Wheel RPM Set", "RPM_WormWheel_Set"),
    ("Worm Wheel RPM Live", "RPM_WormWheel_Live"),
    ("3-Way Valve", "3WayValve"),
    ("Pump PWM", "Pump_PWM"),
    ("Brazier", "Brazier"),
    ("Profile", "Profile"),
    ("Modbus Address", "Modbus_Address"),
    ("Active Live", "Active_Live"),
    ("Firmware Version", "FirmwareVersion"),
    ("Database ID", "DatabaseID"),
    ("Active Temperature", "Active_Temperature"),
    ("Set Boiler", "SetBoiler"),
    ("Set Health", "SetHealth"),
    ("Pellet Sensor", "Pellet_Sensor"),
    ("Celsius Or Fahrenheit", "Celcius_Or_Fahrenheit"),
    ("Sound Effects", "Sound_Effects"),
    ("Sleep", "Sleep"),
    ("AntiFreeze", "AntiFreeze"),
    ("Date Time Hours", "Date_Time_Hours"),
    ("Date Time Minutes", "Date_Time_Minutes"),
    ("Date Day Of Month", "Date_Day_Of_Month"),
    ("Date Month", "Date_Month"),
    ("Date Year", "Date_Year"),
]


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
        MczStateEntity(controller, coordinator, name="State", command_name="state"),
        MczSensorEntity(
            controller,
            coordinator,
            "Temperature",
            "Ambient_Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ]

    for name, command_name in _TEMPERATURE_SENSORS:
        entities.append(
            MczSensorEntity(
                controller,
                coordinator,
                name,
                command_name,
                device_class=SensorDeviceClass.TEMPERATURE,
                unit_of_measurement=UnitOfTemperature.CELSIUS,
            )
        )

    for name, command_name in _MAIN_SENSORS:
        entities.append(MczSensorEntity(controller, coordinator, name, command_name))

    for name, command_name in _DIAGNOSTIC_SENSORS:
        entities.append(
            MczSensorEntity(
                controller,
                coordinator,
                name,
                command_name,
                entity_category=EntityCategory.DIAGNOSTIC,
            )
        )

    # Safety net: expose any protocol field not already covered above or in
    # climate/switch/number, so a future firmware/protocol addition still surfaces
    # instead of silently staying attribute-only.
    known = _ALREADY_EXPOSED | {c for _, c in _TEMPERATURE_SENSORS}
    known |= {c for _, c in _MAIN_SENSORS}
    known |= {c for _, c in _DIAGNOSTIC_SENSORS}
    known |= {"Ambient_Temperature", "Power", "Diagnostics"}
    for command_name in coordinator.data:
        if command_name not in known:
            entities.append(
                MczSensorEntity(
                    controller,
                    coordinator,
                    command_name.replace("_", " "),
                    command_name,
                    entity_category=EntityCategory.DIAGNOSTIC,
                )
            )

    if entities:
        async_add_entities(entities)


class MczStateEntity(MczEntity, SensorEntity):
    """Representation of a debug sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> str:
        """Return the state."""
        _LOGGER.debug("State entity debug")
        _LOGGER.debug(self.coordinator.data)
        if "Stove_State" in self.coordinator.data:
            return get_maestro_state_description(
                int(self.coordinator.data["Stove_State"])
            )
        return "unknown"

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        if self.coordinator.data:
            return self.coordinator.data
        return {}


class MczSensorEntity(MczEntity, SensorEntity):
    """Representation of a MCZ sensor."""

    def __init__(
        self,
        controller: MaestroController,
        coordinator,
        name,
        command_name,
        device_class: SensorDeviceClass | None = None,
        unit_of_measurement: str | None = None,
        entity_category: EntityCategory | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(controller, coordinator, name, command_name)
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit_of_measurement
        if entity_category is not None:
            self._attr_entity_category = entity_category

    @property
    def native_value(self) -> Any:
        """Return the state."""
        return self.coordinator.data.get(self._command_name)
