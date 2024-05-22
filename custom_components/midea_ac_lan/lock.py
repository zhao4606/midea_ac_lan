from homeassistant.components.lock import LockEntity
from homeassistant.const import CONF_DEVICE_ID, CONF_SWITCHES, Platform

from .const import DEVICES, DOMAIN
from .midea_devices import MIDEA_DEVICES
from .midea_entity import MideaEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    device_id = config_entry.data.get(CONF_DEVICE_ID)
    device = hass.data[DOMAIN][DEVICES].get(device_id)
    extra_switches = config_entry.options.get(CONF_SWITCHES, [])
    locks = []
    for entity_key, config in MIDEA_DEVICES[device.device_type]["entities"].items():
        if config["type"] == Platform.LOCK and entity_key in extra_switches:
            dev = MideaLock(device, entity_key)
            locks.append(dev)
    async_add_entities(locks)


class MideaLock(MideaEntity, LockEntity):

    @property
    def is_locked(self):
        return self._device.get_attribute(self._entity_key)

    def lock(self, **kwargs) -> None:
        self._device.set_attribute(attr=self._entity_key, value=True)

    def unlock(self, **kwargs) -> None:
        self._device.set_attribute(attr=self._entity_key, value=False)

    def open(self, **kwargs) -> None:
        self.async_unlock()
