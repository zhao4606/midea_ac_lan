import logging
from typing import Any, TypeAlias, cast

from midealocal.devices.a1 import MideaA1Device
from midealocal.devices.fd import MideaFDDevice

from homeassistant.components.humidifier import (
    HumidifierDeviceClass,
    HumidifierEntity,
    HumidifierEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID, CONF_SWITCHES, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICES, DOMAIN
from .midea_devices import MIDEA_DEVICES
from .midea_entity import MideaEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    device_id = config_entry.data.get(CONF_DEVICE_ID)
    device = hass.data[DOMAIN][DEVICES].get(device_id)
    extra_switches = config_entry.options.get(CONF_SWITCHES, [])
    devs: list[MideaA1Humidifier | MideaFDHumidifier] = []
    for entity_key, config in cast(
        dict, MIDEA_DEVICES[device.device_type]["entities"]
    ).items():
        if config["type"] == Platform.HUMIDIFIER and (
            config.get("default") or entity_key in extra_switches
        ):
            if device.device_type == 0xA1:
                devs.append(MideaA1Humidifier(device, entity_key))
            if device.device_type == 0xFD:
                devs.append(MideaFDHumidifier(device, entity_key))
    async_add_entities(devs)


MideaHumidifierDevice: TypeAlias = MideaFDDevice | MideaA1Device


class MideaHumidifier(MideaEntity, HumidifierEntity):
    _device: MideaHumidifierDevice

    def __init__(self, device: MideaHumidifierDevice, entity_key: str) -> None:
        super().__init__(device, entity_key)

    @property
    def target_humidity(self) -> float:
        return cast(float, self._device.get_attribute("target_humidity"))

    @property
    def mode(self) -> str:
        return cast(str, self._device.get_attribute("mode"))

    @property
    def available_modes(self) -> list[str] | None:
        return cast(list, self._device.modes)

    def set_humidity(self, humidity: int) -> None:
        self._device.set_attribute("target_humidity", humidity)

    def set_mode(self, mode: str) -> None:
        self._device.set_attribute("mode", mode)

    @property
    def is_on(self) -> bool:
        return cast(bool, self._device.get_attribute(attr="power"))

    def turn_on(self, **kwargs: Any) -> None:
        self._device.set_attribute(attr="power", value=True)

    def turn_off(self, **kwargs: Any) -> None:
        self._device.set_attribute(attr="power", value=False)

    def update_state(self, status: Any) -> None:
        if self.hass:
            self.schedule_update_ha_state()


class MideaA1Humidifier(MideaHumidifier):
    _device: MideaA1Device

    def __init__(self, device: MideaA1Device, entity_key: str) -> None:
        super().__init__(device, entity_key)
        self._attr_min_humidity: float = 35
        self._attr_max_humidity: float = 85

    @property
    def device_class(self) -> HumidifierDeviceClass:
        return HumidifierDeviceClass.DEHUMIDIFIER

    @property
    def supported_features(self) -> HumidifierEntityFeature:
        return HumidifierEntityFeature.MODES


class MideaFDHumidifier(MideaHumidifier):
    _device: MideaFDDevice

    def __init__(self, device: MideaFDDevice, entity_key: str) -> None:
        super().__init__(device, entity_key)
        self._attr_min_humidity: float = 35
        self._attr_max_humidity: float = 85

    @property
    def device_class(self) -> HumidifierDeviceClass:
        return HumidifierDeviceClass.HUMIDIFIER

    @property
    def supported_features(self) -> HumidifierEntityFeature:
        return HumidifierEntityFeature.MODES
