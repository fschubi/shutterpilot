from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_GLOBAL_AUTO, CONF_DEFAULT_VPOS, CONF_DEFAULT_COOLDOWN

class ShutterPilotConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="ShutterPilot", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_GLOBAL_AUTO, default=True): bool,
            vol.Required(CONF_DEFAULT_VPOS, default=30): vol.All(int, vol.Range(min=0, max=80)),
            vol.Required(CONF_DEFAULT_COOLDOWN, default=120): vol.All(int, vol.Range(min=0, max=900)),
        })
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ShutterPilotOptionsFlow(config_entry)

class ShutterPilotOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = {**self.entry.data, **self.entry.options}
        schema = vol.Schema({
            vol.Required(CONF_GLOBAL_AUTO, default=data.get(CONF_GLOBAL_AUTO, True)): bool,
            vol.Required(CONF_DEFAULT_VPOS, default=data.get(CONF_DEFAULT_VPOS, 30)): vol.All(int, vol.Range(min=0, max=80)),
            vol.Required(CONF_DEFAULT_COOLDOWN, default=data.get(CONF_DEFAULT_COOLDOWN, 120)): vol.All(int, vol.Range(min=0, max=900)),
        })
        return self.async_show_form(step_id="init", data_schema=schema)
