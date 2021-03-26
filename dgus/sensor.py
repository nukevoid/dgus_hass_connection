from .const import (
    DOMAIN,
    CONF_SCREENS
)
from typing import Any, Callable, Dict, Optional
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)

import serial

async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    sensors = [DGUSSensor(screen) for screen in config[CONF_SCREENS]]
    async_add_entities(sensors, update_before_add=True)

class DGUSSensor(Entity):
    def __init__(self, screen):
        self._state = None

    @property
    def name(self):
        return 'DGUS screen'

    @property
    def state(self):
        return self._state

    def update(self):
        pass
        #self._state = self.hass.data[DOMAIN]['temperature']