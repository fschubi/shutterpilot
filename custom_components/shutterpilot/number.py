from __future__ import annotations
from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN, CONF_DEFAULT_VPOS

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    async_add_entities([ShutterPilotDefaultVPosNumber(hass, entry)], True)

class ShutterPilotDefaultVPosNumber(NumberEntity):
    _attr_has_entity_name = True
    _attr_native_min_value = 0
    _attr_native_max_value = 80
    _attr_native_step = 1
    _attr_mode = "slider"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_default_vpos"
        self._value = int(entry.options.get(CONF_DEFAULT_VPOS, entry.data.get(CONF_DEFAULT_VPOS, 30)))

    @property
    def name(self):
        return "Standard Lüftungsposition (%)"

    @property
    def native_value(self) -> float:
        return float(self._value)

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name="ShutterPilot",
            manufacturer="ShutterPilot",
            model="Core",
        )

    async def async_set_native_value(self, value: float) -> None:
        self._value = int(value)
        new_opts = dict(self.entry.options)
        new_opts[CONF_DEFAULT_VPOS] = self._value
        self.hass.config_entries.async_update_entry(self.entry, options=new_opts)
        self.async_write_ha_state()

    @callback
    def async_update(self):
        self._value = int(self.entry.options.get(CONF_DEFAULT_VPOS, self._value))
