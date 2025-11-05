from __future__ import annotations
import logging
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from .const import (
    DOMAIN, CONF_PROFILES, RUNTIME_PROFILES, P_NAME, P_COVER
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up sensors for ShutterPilot."""
    entities = []
    
    # Create config sensor (for management card)
    entities.append(ShutterPilotConfigSensor(hass, entry))
    
    # Create profile-specific sensors
    store = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if store:
        runtime_profiles = store.get(RUNTIME_PROFILES, [])
        for profile_controller in runtime_profiles:
            try:
                profile_name = profile_controller.name
                entities.extend([
                    ShutterPilotStatusSensor(hass, entry, profile_controller),
                    ShutterPilotLastActionSensor(hass, entry, profile_controller),
                    ShutterPilotCooldownRemainingSensor(hass, entry, profile_controller),
                    ShutterPilotSunElevationSensor(hass, entry, profile_controller),
                ])
                _LOGGER.debug("Created sensors for profile: %s", profile_name)
            except Exception as ex:
                _LOGGER.exception("Failed to create sensors for profile %s: %s", 
                                profile_controller.name, ex)
    
    async_add_entities(entities, True)


def _sanitize_name(name: str) -> str:
    """Create safe entity name from profile name."""
    safe = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' 
                  for c in name)
    safe = safe.replace(' ', '_').replace('-', '_').lower()
    while '__' in safe:
        safe = safe.replace('__', '_')
    return safe.strip('_')


class ShutterPilotStatusSensor(SensorEntity):
    """Sensor showing current profile status."""
    
    _attr_has_entity_name = True
    _attr_icon = "mdi:state-machine"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, profile_controller):
        """Initialize status sensor."""
        self.hass = hass
        self.entry = entry
        self.profile_controller = profile_controller
        self.profile_name = profile_controller.name
        
        safe_name = _sanitize_name(self.profile_name)
        self._attr_unique_id = f"{entry.entry_id}_status_{safe_name}"
        self._attr_device_class = None
        
        _LOGGER.debug("Initialized status sensor for profile: %s", self.profile_name)

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self.profile_name} Status"

    @property
    def native_value(self) -> str:
        """Return the current status."""
        return self.profile_controller.get_status()

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
            "enabled": self.profile_controller.enabled,
            "cover_entity": self.profile_controller.cover,
        }

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        @callback
        def _update_callback():
            """Update sensor state."""
            self.async_write_ha_state()
        
        self._update_callback = _update_callback
        self.profile_controller.register_sensor_callback(_update_callback)
        
        # Remove callback on unload
        @callback
        def _cleanup():
            if hasattr(self, '_update_callback') and self._update_callback in self.profile_controller._sensor_update_callbacks:
                self.profile_controller._sensor_update_callbacks.remove(self._update_callback)
        
        self.async_on_remove(_cleanup)


class ShutterPilotLastActionSensor(SensorEntity):
    """Sensor showing last action reason."""
    
    _attr_has_entity_name = True
    _attr_icon = "mdi:information"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, profile_controller):
        """Initialize last action sensor."""
        self.hass = hass
        self.entry = entry
        self.profile_controller = profile_controller
        self.profile_name = profile_controller.name
        
        safe_name = _sanitize_name(self.profile_name)
        self._attr_unique_id = f"{entry.entry_id}_last_action_{safe_name}"
        self._attr_device_class = None

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self.profile_name} Letzte Aktion"

    @property
    def native_value(self) -> str:
        """Return the last action reason."""
        reason = self.profile_controller.get_last_action_reason()
        # Translate common reasons to German
        translations = {
            "door_open": "Tür offen",
            "door_opened": "Tür geöffnet",
            "window_open": "Fenster offen",
            "window_opened": "Fenster geöffnet",
            "window_closed_cooldown": "Fenster geschlossen (Cooldown)",
            "cooldown_active": "Cooldown aktiv",
            "sun_shade": "Sonnenbeschattung",
            "night_mode": "Nachtmodus",
            "time_schedule_up": "Zeitplan - Öffnen",
            "time_schedule_down": "Zeitplan - Schließen",
            "default_open": "Standard - Offen",
            "auto_disabled": "Automatik deaktiviert",
            "initialization": "Initialisierung",
            "unknown": "Unbekannt",
        }
        # Check if it's a sun_shade with values
        if reason.startswith("sun_shade_lux_"):
            lux_value = reason.replace("sun_shade_lux_", "")
            return f"Sonnenbeschattung (Lux: {lux_value})"
        elif reason.startswith("sun_shade_temp_"):
            temp_value = reason.replace("sun_shade_temp_", "")
            return f"Sonnenbeschattung (Temp: {temp_value}°C)"
        
        return translations.get(reason, reason)

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
            "raw_reason": self.profile_controller.get_last_action_reason(),
        }

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        @callback
        def _update_callback():
            """Update sensor state."""
            self.async_write_ha_state()
        
        self.profile_controller.register_sensor_callback(_update_callback)
        
        @callback
        def _cleanup():
            if hasattr(self, '_update_callback') and self._update_callback in self.profile_controller._sensor_update_callbacks:
                self.profile_controller._sensor_update_callbacks.remove(self._update_callback)
        
        self.async_on_remove(_cleanup)


class ShutterPilotCooldownRemainingSensor(SensorEntity):
    """Sensor showing remaining cooldown time."""
    
    _attr_has_entity_name = True
    _attr_icon = "mdi:timer-sand"
    _attr_native_unit_of_measurement = "s"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, profile_controller):
        """Initialize cooldown sensor."""
        self.hass = hass
        self.entry = entry
        self.profile_controller = profile_controller
        self.profile_name = profile_controller.name
        
        safe_name = _sanitize_name(self.profile_name)
        self._attr_unique_id = f"{entry.entry_id}_cooldown_{safe_name}"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self.profile_name} Cooldown verbleibend"

    @property
    def native_value(self) -> float:
        """Return remaining cooldown time in seconds."""
        return self.profile_controller.get_cooldown_remaining()

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
        cooldown_remaining = self.profile_controller.get_cooldown_remaining()
        return {
            "profile_name": self.profile_name,
            "cooldown_active": cooldown_remaining > 0,
            "cooldown_total": float(self.profile_controller.cooldown),
        }

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        @callback
        def _update_callback():
            """Update sensor state."""
            self.async_write_ha_state()
        
        self.profile_controller.register_sensor_callback(_update_callback)
        
        @callback
        def _cleanup():
            if hasattr(self, '_update_callback') and self._update_callback in self.profile_controller._sensor_update_callbacks:
                self.profile_controller._sensor_update_callbacks.remove(self._update_callback)
        
        self.async_on_remove(_cleanup)


class ShutterPilotSunElevationSensor(SensorEntity):
    """Sensor showing sun elevation for profile."""
    
    _attr_has_entity_name = True
    _attr_icon = "mdi:sun-thermometer"
    _attr_native_unit_of_measurement = "°"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, profile_controller):
        """Initialize sun elevation sensor."""
        self.hass = hass
        self.entry = entry
        self.profile_controller = profile_controller
        self.profile_name = profile_controller.name
        
        safe_name = _sanitize_name(self.profile_name)
        self._attr_unique_id = f"{entry.entry_id}_sun_elevation_{safe_name}"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self.profile_name} Sonnenstand Elevation"

    @property
    def native_value(self) -> float:
        """Return current sun elevation."""
        elevation, _ = self.profile_controller.get_sun_data()
        return round(elevation, 1)

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
        elevation, azimuth = self.profile_controller.get_sun_data()
        return {
            "profile_name": self.profile_name,
            "azimuth": round(azimuth, 1),
            "azimuth_min": self.profile_controller.az_min,
            "azimuth_max": self.profile_controller.az_max,
            "in_azimuth_range": self.profile_controller.az_min <= azimuth <= self.profile_controller.az_max,
        }

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        @callback
        def _update_callback():
            """Update sensor state."""
            self.async_write_ha_state()
        
        self._update_callback = _update_callback
        # Register callback for status updates (also triggers on sun changes)
        self.profile_controller.register_sensor_callback(_update_callback)
        
        # Also update periodically (every minute) to track sun movement
        from homeassistant.helpers.event import async_track_time_interval
        from datetime import timedelta
        
        @callback
        def _periodic_update(_now):
            """Periodic update for sun tracking."""
            self.async_write_ha_state()
        
        self._periodic_unsub = async_track_time_interval(self.hass, _periodic_update, timedelta(minutes=1))
        
        @callback
        def _cleanup():
            if hasattr(self, '_update_callback') and self._update_callback in self.profile_controller._sensor_update_callbacks:
                self.profile_controller._sensor_update_callbacks.remove(self._update_callback)
            if hasattr(self, '_periodic_unsub'):
                self._periodic_unsub()
        
        self.async_on_remove(_cleanup)


class ShutterPilotConfigSensor(SensorEntity):
    """Sensor that exposes config for the management card."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_registry_enabled_default = False  # Hidden by default

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_config"
        self._attr_name = "Configuration"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"ShutterPilot",
            manufacturer="ShutterPilot",
            model="Configuration",
        )

    @property
    def native_value(self) -> str:
        """Return the state."""
        return "OK"

    @property
    def extra_state_attributes(self) -> dict:
        """Return config as attributes."""
        return {
            "entry_id": self._entry.entry_id,
            "profiles": self._entry.options.get(CONF_PROFILES, []),
            "areas": self._entry.options.get("areas", {}),
            "global_settings": {
                "default_vpos": self._entry.options.get("default_vpos", 30),
                "default_cooldown": self._entry.options.get("default_cooldown", 120),
                "summer_start": self._entry.options.get("summer_start", "05-01"),
                "summer_end": self._entry.options.get("summer_end", "09-30"),
                "sun_elevation_end": self._entry.options.get("sun_elevation_end", 3.0),
                "sun_offset_up": self._entry.options.get("sun_offset_up", 0),
                "sun_offset_down": self._entry.options.get("sun_offset_down", 0),
            }
        }

    async def async_added_to_hass(self) -> None:
        """Register update listener."""
        self._entry.add_update_listener(self._update_listener)

    async def _update_listener(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Handle options update."""
        self.async_write_ha_state()

