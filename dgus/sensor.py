import logging
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
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change
from .dgus_protocol import create_protocol

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    sensors = [DGUSSensor(hass, screen) for screen in config[CONF_SCREENS]]
    async_add_entities(sensors, update_before_add=True)


class StateConverters:
    @staticmethod
    def int(entry, protocol):
        vp = entry['vp']
        return lambda state: protocol.write_vp(vp, int(state))

    @staticmethod 
    def map(entry, protocol):
        vp = entry['vp']
        map_state = entry['map']
        return lambda state: protocol.write_vp(vp, map_state[state])


class DGUSSensor(Entity):
    def __init__(self, hass, screen):
        self._state = None
        self._hass = hass
        self._name = screen['name']
        self._entities_track_handlers = dict()
        try:
            self._protocol = create_protocol(screen['port_name'], screen['bound_rate'], self.on_data)
        except:
            _LOGGER.error("Cant open serial port %s", screen['port_name'])
            return 
        
        if 'show_states' in screen:
            for entry in screen['show_states']:
                converter = getattr(StateConverters, entry['type'])
                self._entities_track_handlers[entry['entity_id']] = converter(entry, self._protocol.protocol)

            entiti_ids = [entry['entity_id'] for entry in screen['show_states']]
            async_track_state_change(hass, entiti_ids, self.state_listener)

    def state_listener(self, entity, old_state, new_state):
        self._entities_track_handlers[entity](new_state)
        
    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    def on_data(self, vp, value):
        eventName = self.name + "_set_vp"
        self._hass.bus.fire(eventName, {"vp": vp, "value": value})
        print(vp, value)

    def update(self):
        pass
