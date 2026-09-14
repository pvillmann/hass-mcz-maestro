"""Entity related."""

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.util import slugify

from .const import DOMAIN
from .maestro import MaestroController


class MczEntity(CoordinatorEntity):
    """Representation of a generic MCZ entity."""

    def __init__(
        self,
        controller: MaestroController,
        coordinator: DataUpdateCoordinator,
        name: str,
        command_name: str,
        translation_key: str | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.controller = controller
        self._command_name = command_name

        if translation_key is not None:
            # Let Home Assistant's translation system supply the display name
            # (strings.json / translations/<lang>.json), following whatever
            # language the HA instance is configured for.
            self._attr_has_entity_name = True
            self._attr_translation_key = translation_key
        else:
            self._attr_name = name
        self._attr_unique_id = slugify(
            f"{DOMAIN}_{controller.host}_{controller.port}_{command_name}"
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN, controller.host + controller.port)},
        }

        self._state = None
