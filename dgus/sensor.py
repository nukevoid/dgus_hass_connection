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
    def extract_attr(state, attr):
        if attr:
            return state.attributes[attr]
        else:
            return state.as_dict()['state']

    @staticmethod
    def send_int(state, settings, protocol):
        vp = settings['vp']
        attr = settings.get('attribute', None)
        try:
            value = int(float(StateConverters.extract_attr(state, attr)))
            protocol.write_vp(vp, value)
        except Exception as er:
             _LOGGER.error("Can't send value: %s", str(er))

    @staticmethod 
    def send_map(state, settings, protocol):
        vp = settings['vp']
        map_state = settings['map']
        attr = settings.get('attribute', None)
        value = map_state[StateConverters.extract_attr(state, attr)]
        protocol.write_vp(vp, value)


class DGUSSensor(Entity):
    def __init__(self, hass, screen):
        self._state = None
        self._hass = hass
        self._name = screen['name']
        self._state_track_settings = {entry['entity_id']:entry for entry in screen.get('show_states',[])}
        try:
            self._protocol = create_protocol(screen['port_name'], screen['bound_rate'], self.on_data)
        except Exception:
            _LOGGER.error("Can't open serial port %s", screen['port_name'])
            return 
        
        entiti_ids = [entry['entity_id'] for entry in screen['show_states']]
        async_track_state_change(hass, entiti_ids, self.state_listener)

    def state_listener(self, entity, old_state, new_state):
        settings = self._state_track_settings[entity]
        if settings['type'] == 'int':
            StateConverters.send_int(new_state, settings, self._protocol.protocol)
        elif settings['type'] == 'map':
            StateConverters.send_map(new_state, settings, self._protocol.protocol)
        
    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    def on_data(self, vp, value):
        eventName = self.name + "_set_vp"
        self._hass.bus.fire(eventName, {"vp": vp, "value": value})

    def update(self):
        pass
