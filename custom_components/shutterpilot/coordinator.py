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
    P_NAME, P_COVER, P_WINDOW, P_DOOR, P_DAY_POS, P_NIGHT_POS, P_VPOS,
    P_DOOR_SAFE, P_LUX, P_TEMP, P_LUX_TH, P_TEMP_TH, P_UP_TIME, P_DOWN_TIME,
    P_AZ_MIN, P_AZ_MAX, P_COOLDOWN, P_ENABLED,
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
        self.az_min = _to_float(cfg.get(P_AZ_MIN, -360), -360)
        self.az_max = _to_float(cfg.get(P_AZ_MAX, 360), 360)
        self.up_time = cfg.get(P_UP_TIME) or ""
        self.down_time = cfg.get(P_DOWN_TIME) or ""
        self.cooldown = _to_int(cfg.get(P_COOLDOWN, entry.options.get(CONF_DEFAULT_COOLDOWN, 120)), 120)
        self.enabled = bool(cfg.get(P_ENABLED, True))

        self._cooldown_until: Optional[datetime] = None
        self._cooldown_timer: Optional[CALLBACK_TYPE] = None
        self._unsubs: list[CALLBACK_TYPE] = []
        
        # Status tracking for sensors
        self._last_action_reason: str = "unknown"
        self._status: str = "inactive"
        self._sensor_update_callbacks: list[CALLBACK_TYPE] = []

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

        # sunrise/sunset + 1-min tick as safety net
        self._unsubs.append(async_track_sunrise(self.hass, self._on_sun_event))
        self._unsubs.append(async_track_sunset(self.hass, self._on_sun_event))
        self._unsubs.append(async_track_time_interval(self.hass, self._on_tick, timedelta(minutes=1)))

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

        # if door open -> safe gap
        if self._is_on(self.door):
            _LOGGER.debug("[%s] Door open → door_safe", self.name)
            self._update_status("active", "door_open")
            await self._set_pos(max(self.vpos, self.door_safe))
            return

        # if window open -> ventilation
        if self._is_on(self.window):
            _LOGGER.debug("[%s] Window open → ventilation", self.name)
            self._update_status("active", "window_open")
            await self._set_pos(self.vpos)
            return

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
        elif should_shade:
            reason = "sun_shade"
            if lux >= self.lux_th:
                reason = f"sun_shade_lux_{int(lux)}"
            elif temp >= self.temp_th:
                reason = f"sun_shade_temp_{temp:.1f}"
            _LOGGER.debug("[%s] Shade (elev=%.1f, az=%.1f, lux=%.0f, temp=%.1f) → day_pos", self.name, elevation, azimuth, lux, temp)
            self._update_status("active", reason)
            await self._set_pos(self.day_pos)
        else:
            _LOGGER.debug("[%s] Default → open", self.name)
            self._update_status("active", "default_open")
            await self.open_cover()

    # ---------- internal listeners ----------
    async def _on_window_change(self, event):
        if not self._auto_allowed():
            return

        to_state = event.data.get("new_state")
        if to_state and to_state.state == STATE_ON:
            # window opened → ventilation; cancel any cooldown timer
            if self._cooldown_timer:
                try:
                    self._cooldown_timer()
                except Exception:
                    pass
                self._cooldown_timer = None
            self._cooldown_until = None
            _LOGGER.debug("[%s] Window opened → ventilation pos=%s", self.name, self.vpos)
            self._update_status("active", "window_opened")
            await self._set_pos(self.vpos)
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
        if to_state and to_state.state == STATE_ON:
            _LOGGER.debug("[%s] Door opened → door_safe", self.name)
            self._update_status("active", "door_opened")
            await self._set_pos(max(self.vpos, self.door_safe))
        else:
            _LOGGER.debug("[%s] Door closed → re-evaluate", self.name)
            await self.evaluate_policy_and_apply()

    async def _on_env_change(self, event):
        await self.evaluate_policy_and_apply()

    async def _on_sun_event(self, *args):
        await self.evaluate_policy_and_apply()

    async def _on_tick(self, now):
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
        
        try:
            domain, srv = service.split(".")
            if self.hass.services.has_service(domain, srv):
                payload = dict(data or {})
                payload["entity_id"] = self.cover
                await self.hass.services.async_call(domain, srv, payload, blocking=False)
                return
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
