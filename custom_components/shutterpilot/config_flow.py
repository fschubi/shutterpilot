from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import *

def _opt(entry):
    return {**entry.data, **entry.options}

def _norm_empty(val):
    return None if (val is None or str(val).strip() == "") else val

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
        self._profiles: list[dict] = list(entry.options.get(CONF_PROFILES, []))  # mutable copy
        self._base_opts: dict = {}
        self._edit_index: int | None = None

    async def async_step_init(self, user_input=None):
        data = _opt(self.entry)

        # Menü inkl. Aktion
        menu = vol.Schema({
            vol.Required(CONF_GLOBAL_AUTO, default=data.get(CONF_GLOBAL_AUTO, True)): bool,
            vol.Required(CONF_DEFAULT_VPOS, default=data.get(CONF_DEFAULT_VPOS, 30)): vol.All(int, vol.Range(min=0, max=80)),
            vol.Required(CONF_DEFAULT_COOLDOWN, default=data.get(CONF_DEFAULT_COOLDOWN, 120)): vol.All(int, vol.Range(min=0, max=900)),
            vol.Optional("action", default="none"): vol.In(["none", "add_profile", "edit_profile", "remove_profile"]),
        })

        if user_input is not None:
            self._base_opts = {
                CONF_GLOBAL_AUTO: user_input[CONF_GLOBAL_AUTO],
                CONF_DEFAULT_VPOS: user_input[CONF_DEFAULT_VPOS],
                CONF_DEFAULT_COOLDOWN: user_input[CONF_DEFAULT_COOLDOWN],
            }
            action = user_input.get("action", "none")
            if action == "add_profile":
                return await self.async_step_add_profile()
            if action == "remove_profile":
                return await self.async_step_remove_profile_select()
            if action == "edit_profile":
                return await self.async_step_edit_profile_select()

            # Speichern ohne Profil-Aktion
            return self.async_create_entry(title="", data={**self._base_opts, CONF_PROFILES: self._profiles})

        # WICHTIG: kein 'description' mehr verwenden → verursachte 500er
        return self.async_show_form(step_id="init", data_schema=menu)

    # ---------- ADD ----------
    async def async_step_add_profile(self, user_input=None):
        schema = vol.Schema({
            vol.Required(P_NAME): str,
            vol.Required(P_COVER): str,         # entity_id: cover.xy
            vol.Optional(P_WINDOW, default=""): str,  # binary_sensor.xy
            vol.Optional(P_DOOR, default=""): str,    # binary_sensor.xy
            vol.Required(P_DAY_POS, default=40): vol.All(int, vol.Range(min=0, max=100)),
            vol.Required(P_NIGHT_POS, default=0): vol.All(int, vol.Range(min=0, max=100)),
            vol.Required(P_VPOS, default=self._base_opts.get(CONF_DEFAULT_VPOS, 30)): vol.All(int, vol.Range(min=0, max=80)),
            vol.Required(P_DOOR_SAFE, default=30): vol.All(int, vol.Range(min=0, max=80)),
            vol.Optional(P_LUX, default=""): str,
            vol.Optional(P_TEMP, default=""): str,
            vol.Optional(P_LUX_TH, default=20000): vol.Coerce(float),
            vol.Optional(P_TEMP_TH, default=26): vol.Coerce(float),
            vol.Optional(P_AZ_MIN, default=-360): vol.Coerce(float),
            vol.Optional(P_AZ_MAX, default=360): vol.Coerce(float),
            vol.Optional(P_UP_TIME, default=""): str,     # "HH:MM"
            vol.Optional(P_DOWN_TIME, default=""): str,   # "HH:MM"
            vol.Optional(P_COOLDOWN, default=self._base_opts.get(CONF_DEFAULT_COOLDOWN, 120)): vol.All(int, vol.Range(min=0, max=1800)),
            vol.Optional(P_ENABLED, default=True): bool,
        })
        if user_input is not None:
            prof = dict(user_input)
            # normalize empties -> None
            for k in (P_WINDOW, P_DOOR, P_LUX, P_TEMP, P_UP_TIME, P_DOWN_TIME):
                prof[k] = _norm_empty(prof.get(k))
            self._profiles.append(prof)
            return await self.async_step_init()
        return self.async_show_form(step_id="add_profile", data_schema=schema)

    # ---------- REMOVE ----------
    async def async_step_remove_profile_select(self, user_input=None):
        if not self._profiles:
            return await self.async_step_init()
        choices = {p.get(P_NAME, f"#{i}"): i for i, p in enumerate(self._profiles)}
        schema = vol.Schema({vol.Required("profile"): vol.In(list(choices.keys()))})
        if user_input is not None:
            idx = choices[user_input["profile"]]
            self._profiles.pop(idx)
            return await self.async_step_init()
        return self.async_show_form(step_id="remove_profile_select", data_schema=schema)

    # ---------- EDIT ----------
    async def async_step_edit_profile_select(self, user_input=None):
        if not self._profiles:
            return await self.async_step_init()
        choices = {p.get(P_NAME, f"#{i}"): i for i, p in enumerate(self._profiles)}
        schema = vol.Schema({vol.Required("profile"): vol.In(list(choices.keys()))})
        if user_input is not None:
            self._edit_index = choices[user_input["profile"]]
            return await self.async_step_edit_profile_form()
        return self.async_show_form(step_id="edit_profile_select", data_schema=schema)

    async def async_step_edit_profile_form(self, user_input=None):
        idx = self._edit_index
        if idx is None or idx < 0 or idx >= len(self._profiles):
            return await self.async_step_init()
        cur = self._profiles[idx]

        schema = vol.Schema({
            vol.Required(P_NAME, default=cur.get(P_NAME, "")): str,
            vol.Required(P_COVER, default=cur.get(P_COVER, "")): str,
            vol.Optional(P_WINDOW, default=cur.get(P_WINDOW) or ""): str,
            vol.Optional(P_DOOR, default=cur.get(P_DOOR) or ""): str,
            vol.Required(P_DAY_POS, default=cur.get(P_DAY_POS, 40)): vol.All(int, vol.Range(min=0, max=100)),
            vol.Required(P_NIGHT_POS, default=cur.get(P_NIGHT_POS, 0)): vol.All(int, vol.Range(min=0, max=100)),
            vol.Required(P_VPOS, default=cur.get(P_VPOS, self._base_opts.get(CONF_DEFAULT_VPOS, 30))): vol.All(int, vol.Range(min=0, max=80)),
            vol.Required(P_DOOR_SAFE, default=cur.get(P_DOOR_SAFE, 30)): vol.All(int, vol.Range(min=0, max=80)),
            vol.Optional(P_LUX, default=cur.get(P_LUX) or ""): str,
            vol.Optional(P_TEMP, default=cur.get(P_TEMP) or ""): str,
            vol.Optional(P_LUX_TH, default=cur.get(P_LUX_TH, 20000)): vol.Coerce(float),
            vol.Optional(P_TEMP_TH, default=cur.get(P_TEMP_TH, 26)): vol.Coerce(float),
            vol.Optional(P_AZ_MIN, default=cur.get(P_AZ_MIN, -360)): vol.Coerce(float),
            vol.Optional(P_AZ_MAX, default=cur.get(P_AZ_MAX, 360)): vol.Coerce(float),
            vol.Optional(P_UP_TIME, default=cur.get(P_UP_TIME) or ""): str,
            vol.Optional(P_DOWN_TIME, default=cur.get(P_DOWN_TIME) or ""): str,
            vol.Optional(P_COOLDOWN, default=cur.get(P_COOLDOWN, self._base_opts.get(CONF_DEFAULT_COOLDOWN, 120))): vol.All(int, vol.Range(min=0, max=1800)),
            vol.Optional(P_ENABLED, default=bool(cur.get(P_ENABLED, True))): bool,
        })
        if user_input is not None:
            newp = dict(user_input)
            for k in (P_WINDOW, P_DOOR, P_LUX, P_TEMP, P_UP_TIME, P_DOWN_TIME):
                newp[k] = _norm_empty(newp.get(k))
            self._profiles[idx] = newp
            # zurück ins Hauptmenü
            return await self.async_step_init()
        return self.async_show_form(step_id="edit_profile_form", data_schema=schema)
