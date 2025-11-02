from __future__ import annotations
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
    async_call_later,  # <- NEU: One-shot Timer für Cooldown-Ende
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
        self._cooldown_timer: Optional[CALLBACK_TYPE] = None  # <- NEU
        self._unsubs: list[CALLBACK_TYPE] = []

    async def async_start(self):
        if not self.cover:
            _LOGGER.warning("Profile %s has no cover_entity_id; skipping", self.name)
            return

        # Subscribe to events
        if self.window:
            self._unsubs.append(
                async_track_state_change_event(self.hass, [self.window], self._on_window_change)
            )
        if self.door:
            self._unsubs.append(
                async_track_state_change_event(self.hass, [self.door], self._on_door_change)
            )
        if self.lux_sensor:
            self._unsubs.append(
                async_track_state_change_event(self.hass, [self.lux_sensor], self._on_env_change)
            )
        if self.temp_sensor:
            self._unsubs.append(
                async_track_state_change_event(self.hass, [self.temp_sensor], self._on_env_change)
            )

        # sunrise/sunset + Tick (lassen wir bei 10 Min., weil Cooldown jetzt aktiv gepuffert wird)
        self._unsubs.append(async_track_sunrise(self.hass, self._on_sun_event))
        self._unsubs.append(async_track_sunset(self.hass, self._on_sun_event))
        self._unsubs.append(async_track_time_interval(self.hass, self._on_tick, timedelta(minutes=10)))

        # First evaluation
        await self.evaluate_policy_and_apply()

        _LOGGER.info("Started profile '%s' for %s", self.name, self.cover)

    async def async_stop(self):
        # Timer abbrechen
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
        # bevorzugt open_cover, sonst Position 100
        await self._svc(
            "cover.open_cover",
            fallback=("cover.set_cover_position", {"position": 100}),
        )

    async def stop_cover(self):
        # wenn stop_cover nicht da: noop
        await self._svc("cover.stop_cover", fallback=None)

    async def close_cover_respecting_rules(self):
        # If door/window open -> only ventilation/max
        if self._is_on(self.door):
            await self._set_pos(max(self.vpos, self.door_safe))
        elif self._is_on(self.window):
            await self._set_pos(self.vpos)
        else:
            # bevorzugt close_cover, sonst Position night_pos
            await self._svc(
                "cover.close_cover",
                fallback=("cover.set_cover_position", {"position": int(self.night_pos)}),
            )

    async def evaluate_policy_and_apply(self):
        """Compute policy and apply considering door/window/cooldown."""
        if not self._auto_allowed():
            return

        # if door open -> safe gap
        if self._is_on(self.door):
            await self._set_pos(max(self.vpos, self.door_safe))
            return

        # if window open -> ventilation
        if self._is_on(self.window):
            await self._set_pos(self.vpos)
            return

        # cooldown after window close -> wait out
        if self._cooldown_until and datetime.now() < self._cooldown_until:
            return

        # Time-based up/down
        now_str = datetime.now().strftime("%H:%M")
        if self.down_time and now_str == self.down_time:
            await self._set_pos(self.night_pos)
            return
        if self.up_time and now_str == self.up_time:
            await self.open_cover()
            return

        # Solar/env policy (über sun.sun)
        sun_state = self.hass.states.get("sun.sun")
        elevation = float(sun_state.attributes.get("elevation", 0)) if sun_state else 0.0
        azimuth = float(sun_state.attributes.get("azimuth", 0)) if sun_state else 0.0

        lux = self._float_state(self.lux_sensor, 0.0)
        temp = self._float_state(self.temp_sensor, 0.0)

        in_az = (self.az_min <= azimuth <= self.az_max)
        should_shade = (elevation > 10 and in_az) and (lux >= self.lux_th or temp >= self.temp_th)

        if elevation < 0:  # night
            await self._set_pos(self.night_pos)
        elif should_shade:
            await self._set_pos(self.day_pos)
        else:
            await self.open_cover()

    # ---------- internal listeners ----------
    async def _on_window_change(self, event):
        if not self._auto_allowed():
            return

        to_state = event.data.get("new_state")
        if to_state and to_state.state == STATE_ON:
            # Fenster geöffnet -> Lüftung, Cooldown-Timer ggf. abbrechen
            if self._cooldown_timer:
                try:
                    self._cooldown_timer()
                except Exception:
                    pass
                self._cooldown_timer = None
            await self._set_pos(self.vpos)
        else:
            # Fenster geschlossen -> Cooldown setzen & One-shot Timer planen
            self._cooldown_until = datetime.now() + timedelta(seconds=max(0, self.cooldown))

            # vorhandenen Timer stoppen
            if self._cooldown_timer:
                try:
                    self._cooldown_timer()
                except Exception:
                    pass
                self._cooldown_timer = None

            # nach Cooldown sofort neu bewerten
            def _after(_now):
                self._cooldown_timer = None
                # async Task starten
                self.hass.async_create_task(self.evaluate_policy_and_apply())

            self._cooldown_timer = async_call_later(self.hass, max(0, self.cooldown), _after)

    async def _on_door_change(self, event):
        if not self._auto_allowed():
            return
        to_state = event.data.get("new_state")
        if to_state and to_state.state == STATE_ON:
            await self._set_pos(max(self.vpos, self.door_safe))
        else:
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

    async def _svc(self, service: str, data: Optional[dict] = None,
                   fallback: tuple[str, dict] | None = None):
        """Rufe einen Dienst auf; wenn nicht vorhanden, nutze optionalen Fallback."""
        if not self.cover:
            return
        domain, srv = service.split(".")
        if self.hass.services.has_service(domain, srv):
            payload = dict(data or {})
            payload["entity_id"] = self.cover
            await self.hass.services.async_call(domain, srv, payload, blocking=False)
            return

        if fallback:
            f_domain, f_srv = fallback[0].split(".")
            f_data = dict(fallback[1])
            f_data["entity_id"] = self.cover
            if self.hass.services.has_service(f_domain, f_srv):
                await self.hass.services.async_call(f_domain, f_srv, f_data, blocking=False)

    async def _set_pos(self, pos: int):
        pos = max(0, min(100, int(pos)))
        await self._svc("cover.set_cover_position", {"position": pos})
