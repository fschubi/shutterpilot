from __future__ import annotations
import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN, CONF_GLOBAL_AUTO, CONF_PROFILES, RUNTIME_PROFILES, P_NAME, P_ENABLED, P_COVER

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up switches for ShutterPilot."""
    entities = [ShutterPilotGlobalAutoSwitch(hass, entry)]
    
    # Create profile-specific switches
    store = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if store:
        runtime_profiles = store.get(RUNTIME_PROFILES, [])
        for profile_controller in runtime_profiles:
            try:
                profile_switch = ShutterPilotProfileSwitch(hass, entry, profile_controller)
                entities.append(profile_switch)
                _LOGGER.debug("Created switch for profile: %s", profile_controller.name)
            except Exception as ex:
                _LOGGER.exception("Failed to create switch for profile %s: %s", 
                                profile_controller.name, ex)
    else:
        # Fallback: create from config if runtime not available yet
        profiles = entry.options.get(CONF_PROFILES, [])
        for idx, profile_cfg in enumerate(profiles):
            try:
                profile_name = profile_cfg.get(P_NAME, f"Profile {idx + 1}")
                profile_switch = ShutterPilotProfileSwitchFromConfig(hass, entry, profile_cfg, idx)
                entities.append(profile_switch)
            except Exception as ex:
                _LOGGER.exception("Failed to create switch for profile %s: %s", profile_name, ex)
    
    async_add_entities(entities, True)

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
    def async_update_callback(self):
        """Update the state when config entry updates."""
        self._is_on = bool(self.entry.options.get(CONF_GLOBAL_AUTO, 
                                                   self.entry.data.get(CONF_GLOBAL_AUTO, True)))
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self.entry.add_update_listener(lambda _: self.async_update_callback())
        )


class ShutterPilotProfileSwitch(SwitchEntity):
    """Switch entity for individual profile enable/disable."""
    
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, profile_controller):
        """Initialize profile switch."""
        self.hass = hass
        self.entry = entry
        self.profile_controller = profile_controller
        self.profile_name = profile_controller.name
        self.profile_index = self._find_profile_index()
        
        # Create unique ID from profile name (sanitized)
        safe_name = self._sanitize_name(self.profile_name)
        self._attr_unique_id = f"{entry.entry_id}_profile_{safe_name}"
        
        # Get initial state from controller
        self._is_on = bool(profile_controller.enabled)
        
        _LOGGER.debug("Initialized profile switch '%s' (enabled=%s)", 
                     self.profile_name, self._is_on)

    def _sanitize_name(self, name: str) -> str:
        """Create safe entity name from profile name."""
        # Replace spaces and special chars with underscores, lowercase
        safe = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' 
                      for c in name)
        safe = safe.replace(' ', '_').replace('-', '_').lower()
        # Remove multiple underscores
        while '__' in safe:
            safe = safe.replace('__', '_')
        return safe.strip('_')

    def _find_profile_index(self) -> int:
        """Find index of profile in config."""
        profiles = self.entry.options.get(CONF_PROFILES, [])
        for idx, p in enumerate(profiles):
            if p.get(P_NAME) == self.profile_name:
                return idx
        return -1

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return f"Automatik {self.profile_name}"

    @property
    def is_on(self) -> bool:
        """Return true if profile is enabled."""
        # Update from controller if available
        if hasattr(self, 'profile_controller') and self.profile_controller:
            self._is_on = bool(self.profile_controller.enabled)
        return self._is_on

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name="ShutterPilot",
            manufacturer="ShutterPilot",
            model="Core",
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        return {
            "profile_name": self.profile_name,
            "cover_entity": self.profile_controller.cover if self.profile_controller else None,
        }

    async def async_turn_on(self, **kwargs):
        """Enable the profile."""
        await self._set_enabled(True)

    async def async_turn_off(self, **kwargs):
        """Disable the profile."""
        await self._set_enabled(False)

    async def _set_enabled(self, value: bool):
        """Update enabled state and persist."""
        try:
            self._is_on = value
            
            # Update controller immediately
            if self.profile_controller:
                self.profile_controller.enabled = value
                _LOGGER.info("Profile '%s' %s via switch", 
                           self.profile_name, "enabled" if value else "disabled")
            
            # Persist to config entry
            await self._persist_profile_enabled(value)
            self.async_write_ha_state()
        except Exception as ex:
            _LOGGER.exception("Error setting profile '%s' enabled to %s: %s", 
                            self.profile_name, value, ex)
            raise

    async def _persist_profile_enabled(self, value: bool):
        """Persist enabled state to config entry options."""
        try:
            profiles = list(self.entry.options.get(CONF_PROFILES, []))
            
            # Find and update the profile
            if self.profile_index >= 0 and self.profile_index < len(profiles):
                profiles[self.profile_index] = {**profiles[self.profile_index], P_ENABLED: value}
            else:
                # Fallback: search by name
                for idx, p in enumerate(profiles):
                    if p.get(P_NAME) == self.profile_name:
                        profiles[idx] = {**p, P_ENABLED: value}
                        self.profile_index = idx
                        break
            
            # Update entry
            new_opts = dict(self.entry.options)
            new_opts[CONF_PROFILES] = profiles
            self.hass.config_entries.async_update_entry(self.entry, options=new_opts)
            
            _LOGGER.debug("Persisted enabled state %s for profile '%s'", 
                        value, self.profile_name)
        except Exception as ex:
            _LOGGER.exception("Error persisting enabled state for profile '%s': %s", 
                            self.profile_name, ex)
            raise

    @callback
    def async_update_callback(self):
        """Update state when config entry updates."""
        # Refresh from controller
        if self.profile_controller:
            self._is_on = bool(self.profile_controller.enabled)
        else:
            # Fallback to config
            profiles = self.entry.options.get(CONF_PROFILES, [])
            if self.profile_index >= 0 and self.profile_index < len(profiles):
                self._is_on = bool(profiles[self.profile_index].get(P_ENABLED, True))
            else:
                # Search by name
                for p in profiles:
                    if p.get(P_NAME) == self.profile_name:
                        self._is_on = bool(p.get(P_ENABLED, True))
                        break
        
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self.entry.add_update_listener(lambda _: self.async_update_callback())
        )


class ShutterPilotProfileSwitchFromConfig(SwitchEntity):
    """Fallback profile switch when controller not available yet."""
    
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, profile_cfg: dict, profile_index: int):
        """Initialize profile switch from config only."""
        self.hass = hass
        self.entry = entry
        self.profile_cfg = profile_cfg
        self.profile_index = profile_index
        self.profile_name = profile_cfg.get(P_NAME, f"Profile {profile_index + 1}")
        
        # Create unique ID
        safe_name = self._sanitize_name(self.profile_name)
        self._attr_unique_id = f"{entry.entry_id}_profile_{safe_name}"
        
        # Get initial state
        self._is_on = bool(profile_cfg.get(P_ENABLED, True))
        
        _LOGGER.debug("Initialized profile switch from config '%s' (enabled=%s)", 
                     self.profile_name, self._is_on)

    def _sanitize_name(self, name: str) -> str:
        """Create safe entity name from profile name."""
        safe = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' 
                      for c in name)
        safe = safe.replace(' ', '_').replace('-', '_').lower()
        while '__' in safe:
            safe = safe.replace('__', '_')
        return safe.strip('_')

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return f"Automatik {self.profile_name}"

    @property
    def is_on(self) -> bool:
        """Return true if profile is enabled."""
        # Update from config
        profiles = self.entry.options.get(CONF_PROFILES, [])
        if self.profile_index < len(profiles):
            self._is_on = bool(profiles[self.profile_index].get(P_ENABLED, True))
        return self._is_on

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name="ShutterPilot",
            manufacturer="ShutterPilot",
            model="Core",
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        return {
            "profile_name": self.profile_name,
            "cover_entity": self.profile_cfg.get(P_COVER),
        }

    async def async_turn_on(self, **kwargs):
        """Enable the profile."""
        await self._set_enabled(True)

    async def async_turn_off(self, **kwargs):
        """Disable the profile."""
        await self._set_enabled(False)

    async def _set_enabled(self, value: bool):
        """Update enabled state and persist."""
        try:
            self._is_on = value
            
            # Update and persist to config entry
            profiles = list(self.entry.options.get(CONF_PROFILES, []))
            if self.profile_index < len(profiles):
                profiles[self.profile_index] = {**profiles[self.profile_index], P_ENABLED: value}
                
                new_opts = dict(self.entry.options)
                new_opts[CONF_PROFILES] = profiles
                self.hass.config_entries.async_update_entry(self.entry, options=new_opts)
                
                _LOGGER.info("Profile '%s' %s via switch (from config)", 
                           self.profile_name, "enabled" if value else "disabled")
            
            self.async_write_ha_state()
        except Exception as ex:
            _LOGGER.exception("Error setting profile '%s' enabled to %s: %s", 
                            self.profile_name, value, ex)
            raise

    @callback
    def async_update_callback(self):
        """Update state when config entry updates."""
        profiles = self.entry.options.get(CONF_PROFILES, [])
        if self.profile_index < len(profiles):
            self._is_on = bool(profiles[self.profile_index].get(P_ENABLED, True))
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self.entry.add_update_listener(lambda _: self.async_update_callback())
        )