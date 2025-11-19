from __future__ import annotations
import asyncio
import logging
from datetime import timedelta, datetime
from typing import Optional

from homeassistant.core import HomeAssistant, CALLBACK_TYPE
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_sunrise,
    async_track_sunset,
    async_track_time_interval,
    async_call_later,
)

from .const import (
    CONF_GLOBAL_AUTO, CONF_DEFAULT_VPOS, CONF_DEFAULT_COOLDOWN,
    CONF_AREAS, CONF_SUMMER_START, CONF_SUMMER_END, CONF_SUN_ELEVATION_END,
    CONF_SUN_OFFSET_UP, CONF_SUN_OFFSET_DOWN,
    AREA_LIVING, AREA_SLEEPING, AREA_CHILDREN,
    A_NAME, A_MODE, A_UP_TIME_WEEK, A_DOWN_TIME_WEEK, A_UP_TIME_WEEKEND,
    A_DOWN_TIME_WEEKEND, A_UP_EARLIEST, A_UP_LATEST, A_STAGGER_DELAY,
    A_BRIGHTNESS_SENSOR, A_BRIGHTNESS_DOWN, A_BRIGHTNESS_UP,
    MODE_TIME_ONLY, MODE_SUN, MODE_GOLDEN_HOUR, MODE_BRIGHTNESS,
    P_NAME, P_COVER, P_AREA, P_WINDOW, P_DOOR, P_DAY_POS, P_NIGHT_POS, P_VPOS,
    P_DOOR_SAFE, P_LUX, P_TEMP, P_LUX_TH, P_TEMP_TH, P_LUX_HYSTERESIS, P_TEMP_HYSTERESIS,
    P_UP_TIME, P_DOWN_TIME, P_AZ_MIN, P_AZ_MAX, P_COOLDOWN, P_ENABLED,
    P_WINDOW_OPEN_DELAY, P_WINDOW_CLOSE_DELAY, P_INTERMEDIATE_POS, P_INTERMEDIATE_TIME,
    P_HEAT_PROTECTION, P_HEAT_PROTECTION_TEMP, P_KEEP_SUNPROTECT, P_BRIGHTNESS_END_DELAY,
    P_NO_CLOSE_SUMMER,
    P_LIGHT_ENTITY, P_LIGHT_BRIGHTNESS, P_LIGHT_ON_SHADE, P_LIGHT_ON_NIGHT,
)

_LOGGER = logging.getLogger(__name__)

def _to_int(val, default):
    try:
        return int(val)
    except Exception:
        return default

def _to_float(val, default):
    try:
        return float(val)
    except Exception:
        return default


class ProfileController:
    """Controls one existing cover entity according to rules."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, cfg: dict):
        self.hass = hass
        self.entry = entry
        self.cfg = cfg
        self.name = cfg.get(P_NAME, "Cover")
        self.cover = cfg.get(P_COVER)
        self.area = cfg.get(P_AREA, "none")  # Bereichs-Zuordnung
        self.window = cfg.get(P_WINDOW) or None
        self.door = cfg.get(P_DOOR) or None
        self.day_pos = _to_int(cfg.get(P_DAY_POS, 40), 40)
        self.night_pos = _to_int(cfg.get(P_NIGHT_POS, 0), 0)
        self.vpos = _to_int(cfg.get(P_VPOS, entry.options.get(CONF_DEFAULT_VPOS, 30)), 30)
        self.door_safe = _to_int(cfg.get(P_DOOR_SAFE, self.vpos), self.vpos)
        self.lux_sensor = cfg.get(P_LUX) or None
        self.temp_sensor = cfg.get(P_TEMP) or None
        self.lux_th = _to_float(cfg.get(P_LUX_TH, 20000), 20000)
        self.temp_th = _to_float(cfg.get(P_TEMP_TH, 26), 26)
        self.lux_hysteresis = _to_int(cfg.get(P_LUX_HYSTERESIS, 20), 20)
        self.temp_hysteresis = _to_int(cfg.get(P_TEMP_HYSTERESIS, 10), 10)
        self.az_min = _to_float(cfg.get(P_AZ_MIN, -360), -360)
        self.az_max = _to_float(cfg.get(P_AZ_MAX, 360), 360)
        self.up_time = cfg.get(P_UP_TIME) or ""
        self.down_time = cfg.get(P_DOWN_TIME) or ""
        self.cooldown = _to_int(cfg.get(P_COOLDOWN, entry.options.get(CONF_DEFAULT_COOLDOWN, 120)), 120)
        self.enabled = bool(cfg.get(P_ENABLED, True))
        
        # Erweiterte Features
        self.window_open_delay = _to_int(cfg.get(P_WINDOW_OPEN_DELAY, 0), 0)
        self.window_close_delay = _to_int(cfg.get(P_WINDOW_CLOSE_DELAY, 0), 0)
        self.intermediate_pos = _to_int(cfg.get(P_INTERMEDIATE_POS, 0), 0)
        self.intermediate_time = cfg.get(P_INTERMEDIATE_TIME) or ""
        self.heat_protection = bool(cfg.get(P_HEAT_PROTECTION, False))
        self.heat_protection_temp = _to_float(cfg.get(P_HEAT_PROTECTION_TEMP, 30), 30)
        self.keep_sunprotect = bool(cfg.get(P_KEEP_SUNPROTECT, False))
        self.brightness_end_delay = _to_int(cfg.get(P_BRIGHTNESS_END_DELAY, 0), 0)
        self.no_close_summer = bool(cfg.get(P_NO_CLOSE_SUMMER, False))
        
        # Light automation
        self.light_entity = cfg.get(P_LIGHT_ENTITY) or None
        self.light_brightness = _to_int(cfg.get(P_LIGHT_BRIGHTNESS, 80), 80)
        self.light_on_shade = bool(cfg.get(P_LIGHT_ON_SHADE, True))
        self.light_on_night = bool(cfg.get(P_LIGHT_ON_NIGHT, True))
        
        # Lade Bereichs-Konfiguration
        self._area_config = self._get_area_config()

        self._cooldown_until: Optional[datetime] = None
        self._cooldown_timer: Optional[CALLBACK_TYPE] = None
        self._unsubs: list[CALLBACK_TYPE] = []
        
        # Status tracking for sensors
        self._last_action_reason: str = "unknown"
        self._status: str = "inactive"
        self._sensor_update_callbacks: list[CALLBACK_TYPE] = []
        
        # Hysterese-Tracking
        self._last_lux_trigger_active: Optional[bool] = None
        self._last_temp_trigger_active: Optional[bool] = None
        self._brightness_end_timer: Optional[CALLBACK_TYPE] = None
        
        # Trigger-basiertes System (wie input_boolean.rolladen_triggered in den Original-Automationen)
        self._system_is_moving_cover: bool = False  # Flag: Wir bewegen gerade den Rollladen
        self._triggered_up: bool = False  # Flag: System hat HOCH getriggert (darf nicht nochmal hoch bis Reset)
        self._triggered_down: bool = False  # Flag: System hat RUNTER getriggert (darf nicht nochmal runter bis Reset)
        self._window_not_close: bool = False  # Flag: Rollladen ist unten, Fenster/Tür-Logik aktiv (wie input_boolean.window_not_close)
        self._last_cover_position: Optional[int] = None  # Letzte bekannte Position
        self._reset_timer: Optional[CALLBACK_TYPE] = None  # Timer für tägliches Reset

    async def async_start(self):
        if not self.cover:
            _LOGGER.warning("Profile %s has no cover_entity_id; skipping", self.name)
            return
        
        # Note: We do NOT validate entity existence at startup anymore
        # Entities might not be loaded yet during HA startup (race condition)
        # Validation happens during actual operations instead
        _LOGGER.debug("Profile %s: Starting (entity validation deferred to runtime)", self.name)

        # Subscribe to events
        if self.window:
            self._unsubs.append(async_track_state_change_event(self.hass, [self.window], self._on_window_change))
        if self.door:
            self._unsubs.append(async_track_state_change_event(self.hass, [self.door], self._on_door_change))
        if self.lux_sensor:
            self._unsubs.append(async_track_state_change_event(self.hass, [self.lux_sensor], self._on_env_change))
        if self.temp_sensor:
            self._unsubs.append(async_track_state_change_event(self.hass, [self.temp_sensor], self._on_env_change))
        
        # Subscribe to area brightness sensor if in brightness mode
        area_mode = self._area_config.get(A_MODE, MODE_TIME_ONLY)
        area_brightness_sensor = self._area_config.get(A_BRIGHTNESS_SENSOR)
        if area_mode == MODE_BRIGHTNESS and area_brightness_sensor:
            self._unsubs.append(async_track_state_change_event(self.hass, [area_brightness_sensor], self._on_env_change))
            _LOGGER.debug("Profile %s: Subscribed to area brightness sensor %s", self.name, area_brightness_sensor)
        
        # Subscribe to cover state changes to detect manual changes
        self._unsubs.append(async_track_state_change_event(self.hass, [self.cover], self._on_cover_change))
        _LOGGER.debug("Profile %s: Subscribed to cover state changes for manual change detection", self.name)

        # sunrise/sunset + 1-min tick as safety net
        self._unsubs.append(async_track_sunrise(self.hass, self._on_sun_event))
        self._unsubs.append(async_track_sunset(self.hass, self._on_sun_event))
        self._unsubs.append(async_track_time_interval(self.hass, self._on_tick, timedelta(minutes=1)))
        
        # Tägliches Reset um 3 Uhr (wie in der Original-Automation)
        from homeassistant.helpers.event import async_track_time_change
        self._unsubs.append(async_track_time_change(self.hass, self._on_daily_reset, hour=3, minute=0, second=0))
        _LOGGER.debug("Profile %s: Scheduled daily reset at 03:00", self.name)

        # First evaluation
        self._update_status("active", "initialization")
        await self.evaluate_policy_and_apply()
        _LOGGER.info("Started profile '%s' for %s (cooldown=%ss)", self.name, self.cover, self.cooldown)

    async def async_stop(self):
        # cancel cooldown timer if any
        if self._cooldown_timer:
            try:
                self._cooldown_timer()
            except Exception:
                pass
            self._cooldown_timer = None

        for u in self._unsubs:
            try:
                u()
            except Exception:
                pass
        self._unsubs.clear()

    # ---------- public actions ----------
    async def open_cover(self):
        if not self._validate_cover_exists():
            return
        await self._svc("cover.open_cover", fallback=("cover.set_cover_position", {"position": 100}))

    async def stop_cover(self):
        if not self._validate_cover_exists():
            return
        await self._svc("cover.stop_cover", fallback=None)

    async def close_cover_respecting_rules(self):
        if not self._validate_cover_exists():
            return
        if self._is_on(self.door):
            await self._set_pos(max(self.vpos, self.door_safe))
        elif self._is_on(self.window):
            await self._set_pos(self.vpos)
        else:
            await self._svc("cover.close_cover", fallback=("cover.set_cover_position", {"position": int(self.night_pos)}))

    async def evaluate_policy_and_apply(self):
        """Compute policy and apply considering door/window/cooldown."""
        if not self._auto_allowed():
            _LOGGER.debug("[%s] Auto disabled, skipping", self.name)
            self._update_status("inactive", "auto_disabled")
            return
        
        # Validate cover exists before doing anything
        if not self._validate_cover_exists():
            self._update_status("inactive", "cover_not_found")
            return

        # TÜR-AUSSPERRSCHUTZ: IMMER aktiv (unabhängig von window_not_close)
        if self.door:
            door_state_obj = self.hass.states.get(self.door)
            if door_state_obj:
                door_state = door_state_obj.state
                if door_state == "open" or (door_state == STATE_ON):
                    # Tür komplett offen → Aussperrschutz
                    _LOGGER.debug("[%s] Door OPEN → door_safe (Aussperrschutz)", self.name)
                    self._update_status("active", "door_open")
                    await self._set_pos(self.door_safe)
                    return
                elif door_state == "tilted" and self._window_not_close:
                    # Tür gekippt UND Fenster-Logik aktiv → Lüftungsposition
                    _LOGGER.debug("[%s] Door TILTED + window_not_close=True → ventilation", self.name)
                    self._update_status("active", "door_tilted")
                    await self._set_pos(self.vpos)
                    return

        # FENSTER-LOGIK: Nur aktiv wenn Rollladen unten/runtergefahren ist (window_not_close = True)
        if self._is_on(self.window) and self._window_not_close:
            _LOGGER.debug("[%s] Window open + window_not_close=True → ventilation", self.name)
            self._update_status("active", "window_open")
            await self._set_pos(self.vpos)
            return
        elif self._is_on(self.window) and not self._window_not_close:
            _LOGGER.debug("[%s] Window open but window_not_close=False (cover is up) → ignoring", self.name)
            # Rollladen ist oben, Fenster-Öffnung wird ignoriert
            pass

        # cooldown after window close -> wait out
        if self._cooldown_until and datetime.now() < self._cooldown_until:
            left = (self._cooldown_until - datetime.now()).total_seconds()
            _LOGGER.debug("[%s] Cooldown active (%.1fs left), skip", self.name, left)
            self._update_status("cooldown", "cooldown_active")
            return

        try:
            now_str = datetime.now().strftime("%H:%M")
        except Exception as ex:
            _LOGGER.warning("[%s] Error getting current time: %s", self.name, ex)
            now_str = ""
        
        if self.down_time and now_str == self.down_time:
            _LOGGER.debug("[%s] Time match down_time=%s → night_pos", self.name, self.down_time)
            self._update_status("active", "time_schedule_down")
            await self._set_pos(self.night_pos)
            return
        if self.up_time and now_str == self.up_time:
            _LOGGER.debug("[%s] Time match up_time=%s → open", self.name, self.up_time)
            self._update_status("active", "time_schedule_up")
            await self.open_cover()
            return
        
        # Helligkeits-basierte Steuerung (wenn Bereich im Brightness-Modus)
        area_mode = self._area_config.get(A_MODE, MODE_TIME_ONLY)
        if area_mode == MODE_BRIGHTNESS:
            area_brightness_sensor = self._area_config.get(A_BRIGHTNESS_SENSOR)
            brightness_down = _to_float(self._area_config.get(A_BRIGHTNESS_DOWN, 5000), 5000)
            brightness_up = _to_float(self._area_config.get(A_BRIGHTNESS_UP, 15000), 15000)
            
            if area_brightness_sensor:
                current_brightness = self._float_state(area_brightness_sensor, 0.0)
                
                # TRIGGER-SYSTEM (wie in Original-Automationen):
                # - triggered_down = False → Darf runterfahren wenn Lux < down
                # - triggered_up = False → Darf hochfahren wenn Lux > up
                # - Nach Aktion → entsprechendes Flag auf True
                # - Erlaubt manuelle Änderungen JEDERZEIT (Position bleibt)
                # - Reset um 3 Uhr → beide Flags auf False
                
                if current_brightness < brightness_down and not self._triggered_down:
                    # Dunkel UND noch nicht runter getriggert → Rollladen runterfahren
                    # PRÜFE: Ist Fenster/Tür offen? → Nur Lüftungsposition!
                    if self._is_on(self.window) or self._is_on(self.door):
                        _LOGGER.info("[%s] 🌙 Brightness DOWN trigger + Window/Door OPEN → ventilation position", 
                                      self.name)
                        self._update_status("active", "brightness_low_with_window_open")
                        await self._set_pos(self.vpos)
                    else:
                        _LOGGER.info("[%s] 🌙 Brightness DOWN trigger: lux=%.0f < %.0f → closing to night position", 
                                      self.name, current_brightness, brightness_down)
                        self._update_status("active", f"brightness_low_{int(current_brightness)}")
                        await self._set_pos(self.night_pos)
                    
                    self._triggered_down = True  # RUNTER-TRIGGER SETZEN
                    self._triggered_up = False   # HOCH-TRIGGER ZURÜCKSETZEN (kann jetzt wieder hoch)
                    self._window_not_close = True  # FENSTER-LOGIK AKTIVIEREN!
                    
                    # Light automation: Turn on light when dark
                    if self.light_on_night:
                        await self._control_light(True, "brightness_low")
                    return
                elif current_brightness > brightness_up and not self._triggered_up:
                    # Hell UND noch nicht hoch getriggert → Rollladen hochfahren
                    _LOGGER.info("[%s] ☀️ Brightness UP trigger: lux=%.0f > %.0f → opening", 
                                  self.name, current_brightness, brightness_up)
                    self._update_status("active", f"brightness_high_{int(current_brightness)}")
                    self._triggered_up = True    # HOCH-TRIGGER SETZEN
                    self._triggered_down = False # RUNTER-TRIGGER ZURÜCKSETZEN (kann jetzt wieder runter)
                    self._window_not_close = False  # FENSTER-LOGIK DEAKTIVIEREN!
                    await self.open_cover()
                    # Light automation: Turn off light when bright
                    await self._control_light(False, "brightness_high")
                    return
                elif current_brightness >= brightness_down and current_brightness <= brightness_up:
                    # In Hysterese-Bereich → aktuellen Zustand beibehalten
                    _LOGGER.debug("[%s] 🔄 Brightness in range [%.0f - %.0f] → maintaining position", 
                                  self.name, brightness_down, brightness_up)
                    self._update_status("active", f"brightness_hold_{int(current_brightness)}")
                    return
                elif self._triggered_down and current_brightness < brightness_down:
                    # Bereits runtergefahren → keine weitere Aktion
                    _LOGGER.debug("[%s] 🔒 Already triggered DOWN - waiting for UP trigger or manual change", 
                                  self.name)
                    return
                elif self._triggered_up and current_brightness > brightness_up:
                    # Bereits hochgefahren → keine weitere Aktion
                    _LOGGER.debug("[%s] 🔒 Already triggered UP - waiting for DOWN trigger or manual change", 
                                  self.name)
                    return
                else:
                    # Zwischen den Schwellwerten → aktuellen Zustand beibehalten
                    _LOGGER.debug("[%s] Brightness mode: lux=%.0f in range [%.0f - %.0f] → maintaining current state", 
                                  self.name, current_brightness, brightness_down, brightness_up)
                    self._update_status("active", f"brightness_hold_{int(current_brightness)}")
                    return
            else:
                _LOGGER.warning("[%s] Area mode is BRIGHTNESS but no brightness sensor configured!", self.name)

        # Solar/env policy
        sun_state = self.hass.states.get("sun.sun")
        try:
            elevation = float(sun_state.attributes.get("elevation", 0)) if sun_state else 0.0
            azimuth = float(sun_state.attributes.get("azimuth", 0)) if sun_state else 0.0
        except (ValueError, TypeError, AttributeError) as ex:
            _LOGGER.warning("[%s] Error reading sun data: %s; using defaults", self.name, ex)
            elevation = 0.0
            azimuth = 0.0

        lux = self._float_state(self.lux_sensor, 0.0)
        temp = self._float_state(self.temp_sensor, 0.0)

        in_az = (self.az_min <= azimuth <= self.az_max)
        should_shade = (elevation > 10 and in_az) and (lux >= self.lux_th or temp >= self.temp_th)

        if elevation < 0:  # night
            _LOGGER.debug("[%s] Night (elev=%.1f) → night_pos", self.name, elevation)
            self._update_status("active", "night_mode")
            await self._set_pos(self.night_pos)
            # Light automation: Turn on light at night
            if self.light_on_night:
                await self._control_light(True, "night_mode")
        elif should_shade:
            reason = "sun_shade"
            if lux >= self.lux_th:
                reason = f"sun_shade_lux_{int(lux)}"
            elif temp >= self.temp_th:
                reason = f"sun_shade_temp_{temp:.1f}"
            _LOGGER.debug("[%s] Shade (elev=%.1f, az=%.1f, lux=%.0f, temp=%.1f) → day_pos", self.name, elevation, azimuth, lux, temp)
            self._update_status("active", reason)
            await self._set_pos(self.day_pos)
            # Light automation: Turn on light when shading
            if self.light_on_shade:
                await self._control_light(True, "shading")
        else:
            _LOGGER.debug("[%s] Default → open", self.name)
            self._update_status("active", "default_open")
            await self.open_cover()
            # Light automation: Turn off light when opening
            await self._control_light(False, "cover_open")

    # ---------- internal listeners ----------
    async def _on_window_change(self, event):
        if not self._auto_allowed():
            return

        to_state = event.data.get("new_state")
        if to_state and to_state.state == STATE_ON:
            # window opened
            # NUR reagieren wenn window_not_close = True (Rollladen ist unten)!
            if self._window_not_close:
                # window opened → ventilation; cancel any cooldown timer
                if self._cooldown_timer:
                    try:
                        self._cooldown_timer()
                    except Exception:
                        pass
                    self._cooldown_timer = None
                self._cooldown_until = None
                _LOGGER.info("[%s] 🪟 Window opened + window_not_close=True → ventilation pos=%s%%", 
                            self.name, self.vpos)
                self._update_status("active", "window_opened")
                await self._set_pos(self.vpos)
            else:
                _LOGGER.info("[%s] 🪟 Window opened but window_not_close=False → ignoring (cover is up)", 
                            self.name)
                # Rollladen ist oben, Fenster wird ignoriert
        else:
            # window closed → plan cooldown
            cd = max(0, int(self.cooldown))
            self._cooldown_until = datetime.now() + timedelta(seconds=cd)
            _LOGGER.debug("[%s] Window closed → start cooldown %ss (until %s)", self.name, cd, self._cooldown_until)
            self._update_status("cooldown", "window_closed_cooldown")

            # cancel existing timer if present
            if self._cooldown_timer:
                try:
                    self._cooldown_timer()
                except Exception:
                    pass
                self._cooldown_timer = None

            if cd <= 1:
                # fast path: evaluate immediately
                self._cooldown_until = None
                self.hass.async_create_task(self.evaluate_policy_and_apply())
            else:
                # schedule evaluation right after cooldown
                def _after(_now):
                    self._cooldown_timer = None
                    self._cooldown_until = None
                    self._update_status("active", "cooldown_expired")
                    self.hass.async_create_task(self.evaluate_policy_and_apply())

                self._cooldown_timer = async_call_later(self.hass, cd, _after)
                
                # Trigger periodic updates during cooldown for sensors
                # This ensures cooldown_remaining sensor updates regularly
                async def _cooldown_ticker():
                    update_interval = min(5, max(1, cd // 20))  # 5s or proportional to cooldown
                    elapsed = 0
                    while elapsed < cd and self._cooldown_until:
                        await asyncio.sleep(update_interval)
                        elapsed += update_interval
                        if self._cooldown_until and datetime.now() < self._cooldown_until:
                            # Trigger sensor update without changing reason
                            for callback in self._sensor_update_callbacks:
                                try:
                                    callback()
                                except Exception as ex:
                                    _LOGGER.warning("[%s] Error in cooldown ticker callback: %s", self.name, ex)
                        else:
                            break
                
                # Start background task for periodic updates
                try:
                    self.hass.async_create_task(_cooldown_ticker())
                except Exception as ex:
                    _LOGGER.debug("[%s] Could not start cooldown ticker: %s", self.name, ex)

    async def _on_door_change(self, event):
        if not self._auto_allowed():
            return
        to_state = event.data.get("new_state")
        if not to_state:
            return
        
        door_state = to_state.state
        
        # Tür-Logik mit 3 Zuständen:
        # - "closed" = zu → Normal
        # - "tilted" = gekippt → Lüftungsposition (NUR wenn window_not_close = True)
        # - "open" = auf → Aussperrschutz (IMMER, unabhängig von window_not_close!)
        
        if door_state == "open" or (door_state == STATE_ON and not hasattr(to_state, 'attributes')):
            # Tür komplett offen → AUSSPERRSCHUTZ (IMMER aktiv!)
            _LOGGER.info("[%s] 🚪 Door OPEN → Aussperrschutz (door_safe=%d%%)", self.name, self.door_safe)
            self._update_status("active", "door_open_lockout")
            await self._set_pos(self.door_safe)
        elif door_state == "tilted":
            # Tür gekippt → Wie Fenster-Lüftung (NUR wenn window_not_close = True)
            if self._window_not_close:
                _LOGGER.info("[%s] 🚪 Door TILTED + window_not_close=True → ventilation pos=%d%%", 
                            self.name, self.vpos)
                self._update_status("active", "door_tilted")
                await self._set_pos(self.vpos)
            else:
                _LOGGER.info("[%s] 🚪 Door TILTED but window_not_close=False → ignoring (cover is up)", 
                            self.name)
        else:  # "closed" or STATE_OFF
            # Tür geschlossen → Re-evaluate
            _LOGGER.debug("[%s] Door closed → re-evaluate", self.name)
            await self.evaluate_policy_and_apply()

    async def _on_env_change(self, event):
        await self.evaluate_policy_and_apply()
    
    async def _on_cover_change(self, event):
        """Detect manual cover changes - Position wird beibehalten, System wartet auf nächsten Trigger."""
        if not self._auto_allowed():
            return
        
        # Ignore if we are currently moving the cover
        if self._system_is_moving_cover:
            _LOGGER.debug("[%s] Cover change detected but system is moving → ignore", self.name)
            return
        
        to_state = event.data.get("new_state")
        from_state = event.data.get("old_state")
        
        if not to_state or not from_state:
            return
        
        # Check if position changed (manual intervention)
        try:
            old_pos = from_state.attributes.get("current_position")
            new_pos = to_state.attributes.get("current_position")
            
            if old_pos is not None and new_pos is not None:
                old_pos = int(old_pos)
                new_pos = int(new_pos)
                
                # Position changed → manual intervention detected
                if abs(old_pos - new_pos) > 2:  # Ignore tiny changes (noise)
                    _LOGGER.info("[%s] ✋ Manual change detected: %d%% → %d%% → Position wird beibehalten", 
                                self.name, old_pos, new_pos)
                    
                    # TRIGGER-SYSTEM: Flags BLEIBEN wie sie sind!
                    # Manuelle Position wird respektiert bis:
                    # - Nächster Brightness-Trigger (UP oder DOWN)
                    # - Tägliches Reset um 3 Uhr
                    # - Fenster/Tür-Aktion (hat Priorität)
                    
                    _LOGGER.info("[%s] 🔓 Manual position active - automation will resume on next brightness trigger or daily reset at 3am", 
                                self.name)
                    self._update_status("active", "manual_control_active")
        except (ValueError, TypeError, AttributeError) as ex:
            _LOGGER.debug("[%s] Error processing cover change: %s", self.name, ex)

    async def _on_sun_event(self, *args):
        await self.evaluate_policy_and_apply()

    async def _on_tick(self, now):
        await self.evaluate_policy_and_apply()
    
    async def _on_daily_reset(self, now):
        """Tägliches Reset um 3 Uhr - Alle Trigger zurücksetzen (wie Reset Rolladen Trigger Automation)."""
        _LOGGER.info("[%s] 🌅 Daily reset at 03:00 - Resetting all trigger flags", self.name)
        self._triggered_up = False
        self._triggered_down = False
        self._window_not_close = False  # Auch window_not_close zurücksetzen
        self._update_status("active", "daily_reset")
        # Nach Reset: Sofort neu evaluieren (kann jetzt wieder fahren)
        await self.evaluate_policy_and_apply()

    # ---------- helpers ----------
    def _is_on(self, entity_id: Optional[str]) -> bool:
        if not entity_id:
            return False
        st = self.hass.states.get(entity_id)
        return bool(st and st.state == STATE_ON)

    def _float_state(self, entity_id: Optional[str], default: float) -> float:
        if not entity_id:
            return default
        st = self.hass.states.get(entity_id)
        try:
            return float(st.state)
        except Exception:
            return default

    def _auto_allowed(self) -> bool:
        opt = self.entry.options
        return bool(opt.get(CONF_GLOBAL_AUTO, True) and self.enabled)
    
    def _get_area_config(self) -> dict:
        """Lade die Bereichs-Konfiguration für dieses Profil."""
        if self.area == "none" or not self.area:
            return {}
        areas = self.entry.options.get(CONF_AREAS, {})
        return areas.get(self.area, {})
    
    def _validate_cover_exists(self) -> bool:
        """Validate cover entity exists at runtime. Returns True if OK."""
        if not self.cover:
            return False
        cover_state = self.hass.states.get(self.cover)
        if not cover_state:
            # Only log once per minute to avoid spam
            if not hasattr(self, '_last_cover_warning'):
                self._last_cover_warning = datetime.now()
                _LOGGER.warning("[%s] Cover entity %s not found (will retry)", self.name, self.cover)
            elif (datetime.now() - self._last_cover_warning).total_seconds() > 60:
                self._last_cover_warning = datetime.now()
                _LOGGER.warning("[%s] Cover entity %s still not found", self.name, self.cover)
            return False
        return True

    async def _svc(self, service: str, data: Optional[dict] = None,
                   fallback: tuple[str, dict] | None = None):
        """Call a service; if not available, use optional fallback."""
        if not self.cover:
            return
        
        # Set flag to indicate system is moving cover (prevents manual change detection)
        self._system_is_moving_cover = True
        
        try:
            domain, srv = service.split(".")
            if self.hass.services.has_service(domain, srv):
                payload = dict(data or {})
                payload["entity_id"] = self.cover
                await self.hass.services.async_call(domain, srv, payload, blocking=False)
            elif fallback:
                # Try fallback if primary service not available
                f_domain, f_srv = fallback[0].split(".")
                f_data = dict(fallback[1])
                f_data["entity_id"] = self.cover
                if self.hass.services.has_service(f_domain, f_srv):
                    await self.hass.services.async_call(f_domain, f_srv, f_data, blocking=False)
                else:
                    _LOGGER.warning("[%s] Neither %s nor fallback %s available for %s", 
                                  self.name, service, fallback[0], self.cover)
            else:
                _LOGGER.warning("[%s] Service %s not available for %s", 
                              self.name, service, self.cover)
        except Exception as ex:
            _LOGGER.exception("[%s] Error calling service %s for %s: %s", 
                           self.name, service, self.cover, ex)
        finally:
            # Reset flag after a short delay (cover needs time to start moving)
            async def _reset_flag():
                await asyncio.sleep(2)  # 2 seconds should be enough for cover to start
                self._system_is_moving_cover = False
                _LOGGER.debug("[%s] System movement flag reset", self.name)
            
            self.hass.async_create_task(_reset_flag())

    async def _set_pos(self, pos: int):
        pos = max(0, min(100, int(pos)))
        await self._svc("cover.set_cover_position", {"position": pos})
    
    # ---------- Status tracking helpers ----------
    def _update_status(self, status: str, reason: str):
        """Update status and trigger sensor callbacks."""
        self._status = status
        self._last_action_reason = reason
        # Trigger all sensor update callbacks
        for callback in self._sensor_update_callbacks:
            try:
                callback()
            except Exception as ex:
                _LOGGER.warning("[%s] Error in sensor update callback: %s", self.name, ex)
    
    def register_sensor_callback(self, callback: CALLBACK_TYPE):
        """Register a callback to be called when status updates."""
        self._sensor_update_callbacks.append(callback)
    
    def get_status(self) -> str:
        """Get current status."""
        return self._status
    
    def get_last_action_reason(self) -> str:
        """Get last action reason."""
        return self._last_action_reason
    
    def get_cooldown_remaining(self) -> float:
        """Get remaining cooldown time in seconds."""
        if self._cooldown_until and datetime.now() < self._cooldown_until:
            return (self._cooldown_until - datetime.now()).total_seconds()
        return 0.0
    
    def get_sun_data(self) -> tuple[float, float]:
        """Get current sun elevation and azimuth."""
        sun_state = self.hass.states.get("sun.sun")
        try:
            elevation = float(sun_state.attributes.get("elevation", 0)) if sun_state else 0.0
            azimuth = float(sun_state.attributes.get("azimuth", 0)) if sun_state else 0.0
            return (elevation, azimuth)
        except (ValueError, TypeError, AttributeError):
            return (0.0, 0.0)
    
    async def _control_light(self, turn_on: bool, reason: str):
        """Control light based on cover action."""
        if not self.light_entity:
            return  # No light configured
        
        light_state = self.hass.states.get(self.light_entity)
        if not light_state:
            _LOGGER.debug("[%s] Light entity %s not found", self.name, self.light_entity)
            return
        
        try:
            if turn_on:
                # Turn on light with brightness
                brightness = int((self.light_brightness / 100) * 255)  # Convert 0-100% to 0-255
                await self.hass.services.async_call(
                    "light",
                    "turn_on",
                    {
                        "entity_id": self.light_entity,
                        "brightness": brightness,
                    },
                    blocking=False,
                )
                _LOGGER.info("[%s] Light %s turned ON (brightness=%d%%) - Reason: %s", 
                           self.name, self.light_entity, self.light_brightness, reason)
            else:
                # Turn off light
                await self.hass.services.async_call(
                    "light",
                    "turn_off",
                    {"entity_id": self.light_entity},
                    blocking=False,
                )
                _LOGGER.info("[%s] Light %s turned OFF - Reason: %s", 
                           self.name, self.light_entity, reason)
        except Exception as ex:
            _LOGGER.warning("[%s] Error controlling light %s: %s", 
                          self.name, self.light_entity, ex)
