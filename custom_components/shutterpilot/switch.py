from __future__ import annotations
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN, CONF_GLOBAL_AUTO

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    async_add_entities([ShutterPilotGlobalAutoSwitch(hass, entry)], True)

class ShutterPilotGlobalAutoSwitch(SwitchEntity):
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_global_auto"
        self._is_on = bool(entry.options.get(CONF_GLOBAL_AUTO, entry.data.get(CONF_GLOBAL_AUTO, True)))

    @property
    def name(self):
        return "Automatik (global)"

    @property
    def is_on(self) -> bool:
        return self._is_on

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name="ShutterPilot",
            manufacturer="ShutterPilot",
            model="Core",
        )

    async def async_turn_on(self, **kwargs):
        self._is_on = True
        await self._persist_option(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._is_on = False
        await self._persist_option(False)
        self.async_write_ha_state()

    async def _persist_option(self, value: bool):
        new_opts = dict(self.entry.options)
        new_opts[CONF_GLOBAL_AUTO] = value
        self.hass.config_entries.async_update_entry(self.entry, options=new_opts)

    @callback
    def async_update(self):
        # follow options updates
        self._is_on = bool(self.entry.options.get(CONF_GLOBAL_AUTO, self._is_on))
