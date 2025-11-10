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

PLATFORMS: list[Platform] = [Platform.SWITCH, Platform.NUMBER, Platform.SENSOR]  # UI-Entities

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

    async def _update_config(call: ServiceCall):
        """Update config entry options (for card usage)."""
        profiles = call.data.get("profiles", [])
        areas = call.data.get("areas", {})
        
        _LOGGER.info("update_config service called with %d profiles and %d areas", 
                     len(profiles) if profiles else 0, 
                     len(areas) if areas else 0)
        
        # Merge with existing options
        new_options = {**entry.options}
        if profiles is not None:
            new_options[CONF_PROFILES] = profiles
            _LOGGER.debug("Updated profiles: %s", [p.get('name', '?') for p in profiles])
        if areas:
            new_options["areas"] = areas
            _LOGGER.debug("Updated areas: %s", list(areas.keys()))
        
        # Update config entry
        hass.config_entries.async_update_entry(entry, options=new_options)
        _LOGGER.info("Config entry updated, triggering reload...")
        
        # Trigger reload to apply changes
        await hass.config_entries.async_reload(entry.entry_id)
        _LOGGER.info("Integration reloaded successfully")

    hass.services.async_register(DOMAIN, "all_up", _all_up)
    hass.services.async_register(DOMAIN, "all_down", _all_down)
    hass.services.async_register(DOMAIN, "stop", _stop)
    hass.services.async_register(DOMAIN, "recalculate_now", _recalc)
    hass.services.async_register(DOMAIN, "update_config", _update_config)

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
    """Handle config entry update - reload to apply changes."""
    _LOGGER.info("Config entry updated, reloading ShutterPilot integration")
    await hass.config_entries.async_reload(entry.entry_id)
