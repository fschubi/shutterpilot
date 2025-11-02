from __future__ import annotations
from typing import Any
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, RUNTIME_PROFILES, CONF_PROFILES, CONF_GLOBAL_AUTO

async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = {}
    
    # Config Entry Data
    data["config_entry"] = {
        "title": entry.title,
        "domain": entry.domain,
        "entry_id": entry.entry_id,
        "data": dict(entry.data),
        "options": dict(entry.options),
    }
    
    # Global Settings
    options = entry.options
    data["global_settings"] = {
        "global_auto": options.get(CONF_GLOBAL_AUTO, True),
        "default_ventilation_position": options.get("default_ventilation_position", 30),
        "default_cooldown": options.get("default_cooldown", 120),
    }
    
    # Profiles Configuration
    profiles_cfg = options.get(CONF_PROFILES, [])
    data["profiles"] = {
        "count": len(profiles_cfg),
        "profiles": profiles_cfg,
    }
    
    # Runtime Status
    store = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if store:
        runtime_profiles = store.get(RUNTIME_PROFILES, [])
        data["runtime"] = {
            "active_profiles": len(runtime_profiles),
            "profile_status": [],
        }
        
        for ctrl in runtime_profiles:
            # Get current state of related entities
            cover_state = None
            window_state = None
            door_state = None
            lux_state = None
            temp_state = None
            
            if ctrl.cover:
                cover_state_obj = hass.states.get(ctrl.cover)
                cover_state = {
                    "state": cover_state_obj.state if cover_state_obj else "unknown",
                    "position": cover_state_obj.attributes.get("current_position") if cover_state_obj else None,
                }
            
            if ctrl.window:
                window_state_obj = hass.states.get(ctrl.window)
                window_state = window_state_obj.state if window_state_obj else "unknown"
            
            if ctrl.door:
                door_state_obj = hass.states.get(ctrl.door)
                door_state = door_state_obj.state if door_state_obj else "unknown"
            
            if ctrl.lux_sensor:
                lux_state_obj = hass.states.get(ctrl.lux_sensor)
                lux_state = lux_state_obj.state if lux_state_obj else "unknown"
            
            if ctrl.temp_sensor:
                temp_state_obj = hass.states.get(ctrl.temp_sensor)
                temp_state = temp_state_obj.state if temp_state_obj else "unknown"
            
            # Get sun state
            sun_state_obj = hass.states.get("sun.sun")
            sun_data = {}
            if sun_state_obj:
                sun_data = {
                    "state": sun_state_obj.state,
                    "elevation": sun_state_obj.attributes.get("elevation"),
                    "azimuth": sun_state_obj.attributes.get("azimuth"),
                }
            
            profile_status = {
                "name": ctrl.name,
                "cover_entity": ctrl.cover,
                "enabled": ctrl.enabled,
                "cover_state": cover_state,
                "window_state": window_state,
                "door_state": door_state,
                "lux_state": lux_state,
                "temp_state": temp_state,
                "sun_data": sun_data,
                "cooldown_active": ctrl._cooldown_until is not None,
                "cooldown_until": ctrl._cooldown_until.isoformat() if ctrl._cooldown_until else None,
            }
            
            data["runtime"]["profile_status"].append(profile_status)
    
    return data
