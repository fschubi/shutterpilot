from __future__ import annotations
import logging
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.helpers import event as hass_event

from .const import (
    DOMAIN, CONF_PROFILES, CONF_GLOBAL_AUTO, DATA, RUNTIME_PROFILES, UNSUBS,
)
from .coordinator import ProfileController

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SWITCH, Platform.NUMBER]  # UI-Entities

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ShutterPilot from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    store = hass.data[DOMAIN][entry.entry_id] = {DATA:{}, RUNTIME_PROFILES:[], UNSUBS:[]}

    # Start controllers for all profiles defined in options
    profiles = entry.options.get(CONF_PROFILES, [])
    runtime_profiles: list[ProfileController] = []
    for p in profiles:
        try:
            ctrl = ProfileController(hass, entry, p)
            await ctrl.async_start()
            runtime_profiles.append(ctrl)
        except Exception as ex:
            _LOGGER.exception("Failed to start profile %s: %s", p.get("name","?"), ex)

    store[RUNTIME_PROFILES] = runtime_profiles

    # Register services
    async def _all_up(call: ServiceCall):
        for c in store[RUNTIME_PROFILES]:
            await c.open_cover()

    async def _all_down(call: ServiceCall):
        for c in store[RUNTIME_PROFILES]:
            await c.close_cover_respecting_rules()

    async def _stop(call: ServiceCall):
        for c in store[RUNTIME_PROFILES]:
            await c.stop_cover()

    async def _recalc(call: ServiceCall):
        for c in store[RUNTIME_PROFILES]:
            await c.evaluate_policy_and_apply()

    hass.services.async_register(DOMAIN, "all_up", _all_up)
    hass.services.async_register(DOMAIN, "all_down", _all_down)
    hass.services.async_register(DOMAIN, "stop", _stop)
    hass.services.async_register(DOMAIN, "recalculate_now", _recalc)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_entry))
    _LOGGER.info("ShutterPilot setup complete with %d profile(s).", len(runtime_profiles))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    store = hass.data[DOMAIN].get(entry.entry_id)
    if store:
        for c in store.get(RUNTIME_PROFILES, []):
            await c.async_stop()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok

async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
