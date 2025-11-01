from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import *

def _opt(entry):
    return {**entry.data, **entry.options}

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
        self._profiles = list(entry.options.get(CONF_PROFILES, []))

    async def async_step_init(self, user_input=None):
        data = _opt(self.entry)
        menu = vol.Schema({
            vol.Required(CONF_GLOBAL_AUTO, default=data.get(CONF_GLOBAL_AUTO, True)): bool,
            vol.Required(CONF_DEFAULT_VPOS, default=data.get(CONF_DEFAULT_VPOS, 30)): vol.All(int, vol.Range(min=0, max=80)),
            vol.Required(CONF_DEFAULT_COOLDOWN, default=data.get(CONF_DEFAULT_COOLDOWN, 120)): vol.All(int, vol.Range(min=0, max=900)),
            vol.Optional("action", default="none"): vol.In(["none","add_profile","remove_profile"])
        })
        if user_input is not None:
            if user_input.get("action") == "add_profile":
                self._base_opts = {
                    CONF_GLOBAL_AUTO: user_input[CONF_GLOBAL_AUTO],
                    CONF_DEFAULT_VPOS: user_input[CONF_DEFAULT_VPOS],
                    CONF_DEFAULT_COOLDOWN: user_input[CONF_DEFAULT_COOLDOWN],
                }
                return await self.async_step_add_profile()
            if user_input.get("action") == "remove_profile":
                self._base_opts = {
                    CONF_GLOBAL_AUTO: user_input[CONF_GLOBAL_AUTO],
                    CONF_DEFAULT_VPOS: user_input[CONF_DEFAULT_VPOS],
                    CONF_DEFAULT_COOLDOWN: user_input[CONF_DEFAULT_COOLDOWN],
                }
                return await self.async_step_remove_profile()

            # none -> save
            return self.async_create_entry(title="", data={
                **user_input,
                CONF_PROFILES: self._profiles
            })
        return self.async_show_form(step_id="init", data_schema=menu, description_placeholders={
            "profiles": ", ".join([p.get(P_NAME,"?") for p in self._profiles]) or "–"
        })

    async def async_step_add_profile(self, user_input=None):
        schema = vol.Schema({
            vol.Required(P_NAME): str,
            vol.Required(P_COVER): str,         # entity_id: cover.xy
            vol.Optional(P_WINDOW, default=""): str,  # binary_sensor.xy
            vol.Optional(P_DOOR, default=""): str,    # binary_sensor.xy
            vol.Required(P_DAY_POS, default=40): vol.All(int, vol.Range(min=0,max=100)),
            vol.Required(P_NIGHT_POS, default=0): vol.All(int, vol.Range(min=0,max=100)),
            vol.Required(P_VPOS, default=self._base_opts.get(CONF_DEFAULT_VPOS,30)): vol.All(int, vol.Range(min=0,max=80)),
            vol.Required(P_DOOR_SAFE, default=30): vol.All(int, vol.Range(min=0,max=80)),
            vol.Optional(P_LUX, default=""): str,
            vol.Optional(P_TEMP, default=""): str,
            vol.Optional(P_LUX_TH, default=20000): vol.Coerce(float),
            vol.Optional(P_TEMP_TH, default=26): vol.Coerce(float),
            vol.Optional(P_AZ_MIN, default=-360): vol.Coerce(float),
            vol.Optional(P_AZ_MAX, default=360): vol.Coerce(float),
            vol.Optional(P_UP_TIME, default=""): str,     # "HH:MM"
            vol.Optional(P_DOWN_TIME, default=""): str,   # "HH:MM"
            vol.Optional(P_COOLDOWN, default=self._base_opts.get(CONF_DEFAULT_COOLDOWN,120)): vol.All(int, vol.Range(min=0,max=1800)),
            vol.Optional(P_ENABLED, default=True): bool,
        })
        if user_input is not None:
            prof = dict(user_input)
            # Normalize empties to None
            for k in (P_WINDOW,P_DOOR,P_LUX,P_TEMP,P_UP_TIME,P_DOWN_TIME):
                if not prof.get(k): prof[k]=None
            self._profiles.append(prof)
            return await self.async_step_init()
        return self.async_show_form(step_id="add_profile", data_schema=schema)

    async def async_step_remove_profile(self, user_input=None):
        choices = {p.get(P_NAME,f"#{i}"): i for i,p in enumerate(self._profiles)}
        if not choices:
            return await self.async_step_init()
        schema = vol.Schema({ vol.Required("profile"): vol.In(list(choices.keys())) })
        if user_input is not None:
            idx = choices[user_input["profile"]]
            self._profiles.pop(idx)
            return await self.async_step_init()
        return self.async_show_form(step_id="remove_profile", data_schema=schema)
