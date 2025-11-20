from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from .const import *

def _opt(entry):
    return {**entry.data, **entry.options}

def _norm_empty(val):
    return None if (val is None or str(val).strip() == "") else val

def _validate_time(val):
    """Validate time format HH:MM."""
    if not val or val.strip() == "":
        return None
    try:
        parts = val.strip().split(":")
        if len(parts) != 2:
            raise ValueError("Invalid format")
        hour = int(parts[0])
        minute = int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Time out of range")
        return f"{hour:02d}:{minute:02d}"
    except (ValueError, AttributeError):
        return None

def _validate_date(val):
    """Validate date format MM-DD."""
    if not val or val.strip() == "":
        return None
    try:
        parts = val.strip().split("-")
        if len(parts) != 2:
            raise ValueError("Invalid format")
        month = int(parts[0])
        day = int(parts[1])
        if not (1 <= month <= 12 and 1 <= day <= 31):
            raise ValueError("Date out of range")
        return f"{month:02d}-{day:02d}"
    except (ValueError, AttributeError):
        return None

class ShutterPilotConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            # Initialize with default areas
            default_areas = {
                AREA_LIVING: {
                    A_NAME: "Wohnbereich",
                    A_MODE: MODE_SUN,
                    A_UP_TIME_WEEK: "07:00",
                    A_DOWN_TIME_WEEK: "22:00",
                    A_UP_TIME_WEEKEND: "08:00",
                    A_DOWN_TIME_WEEKEND: "23:00",
                    A_UP_EARLIEST: "06:00",
                    A_UP_LATEST: "09:00",
                    A_STAGGER_DELAY: 10,
                    A_BRIGHTNESS_SENSOR: None,
                    A_BRIGHTNESS_DOWN: 5000,
                    A_BRIGHTNESS_UP: 15000,
                },
                AREA_SLEEPING: {
                    A_NAME: "Schlafbereich",
                    A_MODE: MODE_SUN,
                    A_UP_TIME_WEEK: "06:00",
                    A_DOWN_TIME_WEEK: "21:00",
                    A_UP_TIME_WEEKEND: "08:00",
                    A_DOWN_TIME_WEEKEND: "22:00",
                    A_UP_EARLIEST: "05:00",
                    A_UP_LATEST: "08:00",
                    A_STAGGER_DELAY: 10,
                    A_BRIGHTNESS_SENSOR: None,
                    A_BRIGHTNESS_DOWN: 5000,
                    A_BRIGHTNESS_UP: 15000,
                },
                AREA_CHILDREN: {
                    A_NAME: "Kinderbereich",
                    A_MODE: MODE_TIME_ONLY,
                    A_UP_TIME_WEEK: "07:30",
                    A_DOWN_TIME_WEEK: "20:00",
                    A_UP_TIME_WEEKEND: "08:30",
                    A_DOWN_TIME_WEEKEND: "21:00",
                    A_UP_EARLIEST: "06:30",
                    A_UP_LATEST: "09:00",
                    A_STAGGER_DELAY: 10,
                    A_BRIGHTNESS_SENSOR: None,
                    A_BRIGHTNESS_DOWN: 5000,
                    A_BRIGHTNESS_UP: 15000,
                }
            }
            data = {
                **user_input,
                CONF_AREAS: default_areas,
                CONF_SUMMER_START: "05-01",
                CONF_SUMMER_END: "09-30",
                CONF_SUN_ELEVATION_END: 10,
                CONF_SUN_OFFSET_UP: 0,
                CONF_SUN_OFFSET_DOWN: 0
            }
            return self.async_create_entry(title="ShutterPilot", data=data)

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
        self._profiles: list[dict] = list(entry.options.get(CONF_PROFILES, []))
        self._areas: dict = dict(entry.options.get(CONF_AREAS, entry.data.get(CONF_AREAS, {})))
        self._base_opts: dict = {}
        self._edit_index: int | None = None
        self._edit_area: str | None = None
        self._temp_area_data: dict = {}  # Zwischenspeicher für 2-Schritt-Bereichsbearbeitung

    async def async_step_init(self, user_input=None):
        data = _opt(self.entry)

        # Hauptmenü mit Tabs
        menu = vol.Schema({
            vol.Required(CONF_GLOBAL_AUTO, default=data.get(CONF_GLOBAL_AUTO, True)): bool,
            vol.Required(CONF_DEFAULT_VPOS, default=data.get(CONF_DEFAULT_VPOS, 30)): vol.All(int, vol.Range(min=0, max=80)),
            vol.Required(CONF_DEFAULT_COOLDOWN, default=data.get(CONF_DEFAULT_COOLDOWN, 120)): vol.All(int, vol.Range(min=0, max=900)),
            vol.Required(CONF_SUMMER_START, default=data.get(CONF_SUMMER_START, "05-01")): str,
            vol.Required(CONF_SUMMER_END, default=data.get(CONF_SUMMER_END, "09-30")): str,
            vol.Required(CONF_SUN_ELEVATION_END, default=data.get(CONF_SUN_ELEVATION_END, 10)): vol.All(int, vol.Range(min=-10, max=30)),
            vol.Required(CONF_SUN_OFFSET_UP, default=data.get(CONF_SUN_OFFSET_UP, 0)): vol.All(int, vol.Range(min=-120, max=120)),
            vol.Required(CONF_SUN_OFFSET_DOWN, default=data.get(CONF_SUN_OFFSET_DOWN, 0)): vol.All(int, vol.Range(min=-120, max=120)),
            vol.Optional("action", default="none"): vol.In([
                "none",
                "manage_areas",
                "add_profile",
                "edit_profile",
                "remove_profile"
            ]),
        })

        if user_input is not None:
            # Validiere Datumsfelder
            summer_start = _validate_date(user_input.get(CONF_SUMMER_START))
            summer_end = _validate_date(user_input.get(CONF_SUMMER_END))
            
            if not summer_start or not summer_end:
                return self.async_show_form(
                    step_id="init",
                    data_schema=menu,
                    errors={"base": "Ungültiges Datumsformat (erwartet: MM-DD)"}
                )

            self._base_opts = {
                CONF_GLOBAL_AUTO: user_input[CONF_GLOBAL_AUTO],
                CONF_DEFAULT_VPOS: user_input[CONF_DEFAULT_VPOS],
                CONF_DEFAULT_COOLDOWN: user_input[CONF_DEFAULT_COOLDOWN],
                CONF_SUMMER_START: summer_start,
                CONF_SUMMER_END: summer_end,
                CONF_SUN_ELEVATION_END: user_input[CONF_SUN_ELEVATION_END],
                CONF_SUN_OFFSET_UP: user_input[CONF_SUN_OFFSET_UP],
                CONF_SUN_OFFSET_DOWN: user_input[CONF_SUN_OFFSET_DOWN],
            }
            
            action = user_input.get("action", "none")
            if action == "manage_areas":
                return await self.async_step_manage_areas()
            if action == "add_profile":
                return await self.async_step_add_profile()
            if action == "remove_profile":
                return await self.async_step_remove_profile_select()
            if action == "edit_profile":
                return await self.async_step_edit_profile_select()

            # Speichern
            return self.async_create_entry(
                title="",
                data={
                    **self._base_opts,
                    CONF_AREAS: self._areas,
                    CONF_PROFILES: self._profiles
                }
            )

        return self.async_show_form(step_id="init", data_schema=menu)

    # ========== BEREICHS-MANAGEMENT ==========
    
    async def async_step_manage_areas(self, user_input=None):
        """Bereichs-Verwaltung mit dynamischen Bereichen."""
        # Erstelle Menü mit allen vorhandenen Bereichen
        menu_options = {
            "back": "Zurück zum Hauptmenü",
            "add_area": "➕ Neuen Bereich hinzufügen",
        }
        
        # Füge alle vorhandenen Bereiche hinzu
        for area_id, area_config in self._areas.items():
            area_name = area_config.get(A_NAME, area_id)
            # Markiere Standard-Bereiche
            if area_id in DEFAULT_AREAS:
                menu_options[area_id] = f"✏️ Bearbeiten: {area_name}"
            else:
                menu_options[area_id] = f"✏️ {area_name} (Bearbeiten/Löschen)"
        
        menu = vol.Schema({
            vol.Optional("area_action", default="back"): vol.In(menu_options),
        })

        if user_input is not None:
            action = user_input.get("area_action", "back")
            if action == "back":
                return await self.async_step_init()
            elif action == "add_area":
                self._edit_area = None  # Signal: Neuer Bereich
                return await self.async_step_add_area()
            else:
                # Bereich bearbeiten
                self._edit_area = action
                return await self.async_step_edit_area()

        return self.async_show_form(step_id="manage_areas", data_schema=menu)
    
    async def async_step_add_area(self, user_input=None):
        """Neuen Bereich hinzufügen."""
        schema = vol.Schema({
            vol.Required("area_id"): str,
            vol.Required(A_NAME): str,
            vol.Required(A_MODE, default=MODE_SUN): vol.In({
                MODE_TIME_ONLY: "Nur Zeit",
                MODE_SUN: "Zeit mit Sonnenauf-/-untergang",
                MODE_GOLDEN_HOUR: "Zeit mit Golden Hour",
                MODE_BRIGHTNESS: "Helligkeit (Lux-basiert)",
            }),
        })
        
        if user_input is not None:
            # Validiere area_id
            area_id = user_input["area_id"].lower().strip().replace(" ", "_")
            
            # Prüfe ob ID bereits existiert
            if area_id in self._areas:
                return self.async_show_form(
                    step_id="add_area",
                    data_schema=schema,
                    errors={"area_id": "Diese Bereichs-ID existiert bereits"}
                )
            
            # Prüfe auf gültige ID (nur Buchstaben, Zahlen, Underscore)
            if not area_id.replace("_", "").isalnum():
                return self.async_show_form(
                    step_id="add_area",
                    data_schema=schema,
                    errors={"area_id": "Nur Buchstaben, Zahlen und Unterstriche erlaubt"}
                )
            
            # Erstelle neuen Bereich mit Defaults
            self._areas[area_id] = {
                A_NAME: user_input[A_NAME],
                A_MODE: user_input[A_MODE],
                A_UP_TIME_WEEK: "07:00",
                A_DOWN_TIME_WEEK: "22:00",
                A_UP_TIME_WEEKEND: "08:00",
                A_DOWN_TIME_WEEKEND: "23:00",
                A_UP_EARLIEST: "06:00",
                A_UP_LATEST: "09:00",
                A_STAGGER_DELAY: 10,
                A_BRIGHTNESS_SENSOR: None,
                A_BRIGHTNESS_DOWN: 5000,
                A_BRIGHTNESS_UP: 15000,
            }
            
            # Direkt zur Bearbeitung weitergehen
            self._edit_area = area_id
            return await self.async_step_edit_area()
        
        return self.async_show_form(step_id="add_area", data_schema=schema)

    async def async_step_edit_area(self, user_input=None):
        """Bereich bearbeiten - Schritt 1: Name und Modus auswählen."""
        if not self._edit_area:
            return await self.async_step_manage_areas()

        current = self._areas.get(self._edit_area, {})
        
        schema_fields = {
            vol.Required(A_NAME, default=current.get(A_NAME, "")): str,
            vol.Required(A_MODE, default=current.get(A_MODE, MODE_SUN)): vol.In({
                MODE_TIME_ONLY: "Nur Zeit",
                MODE_SUN: "Zeit mit Sonnenauf-/-untergang",
                MODE_GOLDEN_HOUR: "Zeit mit Golden Hour",
                MODE_BRIGHTNESS: "Helligkeit (Lux-basiert)",
            }),
        }

        if self._edit_area not in DEFAULT_AREAS:
            schema_fields[vol.Optional("delete_area", default=False)] = bool
        
        schema = vol.Schema(schema_fields)

        if user_input is not None:
            if user_input.get("delete_area", False):
                assigned_profiles = [p for p in self._profiles if p.get(P_AREA) == self._edit_area]
                if assigned_profiles:
                    return self.async_show_form(
                        step_id="edit_area",
                        data_schema=schema,
                        errors={"base": f"Kann nicht gelöscht werden: {len(assigned_profiles)} Profile sind diesem Bereich zugeordnet"}
                    )
                del self._areas[self._edit_area]
                return await self.async_step_manage_areas()
            
            # Speichere Name und Modus temporär
            self._temp_area_data = {
                A_NAME: user_input[A_NAME],
                A_MODE: user_input[A_MODE],
            }
            
            # Weiter zu Schritt 2: Detail-Konfiguration
            return await self.async_step_edit_area_details()
        
        return self.async_show_form(step_id="edit_area", data_schema=schema)
    
    async def async_step_edit_area_details(self, user_input=None):
        """Bereich bearbeiten - Schritt 2: Detail-Felder basierend auf Modus."""
        if not self._edit_area or not self._temp_area_data:
            return await self.async_step_manage_areas()
        
        current = self._areas.get(self._edit_area, {})
        mode = self._temp_area_data.get(A_MODE, MODE_SUN)
        
        # Dynamische Schema-Felder basierend auf Modus
        schema_fields = {}
        
        if mode == MODE_BRIGHTNESS:
            # Helligkeit-Modus: NUR Helligkeit + Earliest/Latest + Stagger
            schema_fields = {
                vol.Required(A_BRIGHTNESS_SENSOR, default=current.get(A_BRIGHTNESS_SENSOR)): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor", device_class="illuminance")
                ),
                vol.Required(A_BRIGHTNESS_DOWN, default=current.get(A_BRIGHTNESS_DOWN, 5000)): vol.Coerce(float),
                vol.Required(A_BRIGHTNESS_UP, default=current.get(A_BRIGHTNESS_UP, 15000)): vol.Coerce(float),
                vol.Required(A_UP_EARLIEST, default=current.get(A_UP_EARLIEST, "06:00")): str,
                vol.Required(A_UP_LATEST, default=current.get(A_UP_LATEST, "22:00")): str,
                vol.Required(A_STAGGER_DELAY, default=current.get(A_STAGGER_DELAY, 10)): vol.All(int, vol.Range(min=0, max=300)),
            }
        elif mode in [MODE_SUN, MODE_GOLDEN_HOUR]:
            # Sonnenstand/Golden Hour: Zeiten + Earliest/Latest + Stagger
            schema_fields = {
                vol.Required(A_UP_TIME_WEEK, default=current.get(A_UP_TIME_WEEK, "07:00")): str,
                vol.Required(A_DOWN_TIME_WEEK, default=current.get(A_DOWN_TIME_WEEK, "22:00")): str,
                vol.Required(A_UP_TIME_WEEKEND, default=current.get(A_UP_TIME_WEEKEND, "08:00")): str,
                vol.Required(A_DOWN_TIME_WEEKEND, default=current.get(A_DOWN_TIME_WEEKEND, "23:00")): str,
                vol.Required(A_UP_EARLIEST, default=current.get(A_UP_EARLIEST, "06:00")): str,
                vol.Required(A_UP_LATEST, default=current.get(A_UP_LATEST, "09:00")): str,
                vol.Required(A_STAGGER_DELAY, default=current.get(A_STAGGER_DELAY, 10)): vol.All(int, vol.Range(min=0, max=300)),
            }
        else:  # MODE_TIME_ONLY
            # Nur Zeit: NUR Zeiten + Stagger (KEINE Earliest/Latest)
            schema_fields = {
                vol.Required(A_UP_TIME_WEEK, default=current.get(A_UP_TIME_WEEK, "07:00")): str,
                vol.Required(A_DOWN_TIME_WEEK, default=current.get(A_DOWN_TIME_WEEK, "22:00")): str,
                vol.Required(A_UP_TIME_WEEKEND, default=current.get(A_UP_TIME_WEEKEND, "08:00")): str,
                vol.Required(A_DOWN_TIME_WEEKEND, default=current.get(A_DOWN_TIME_WEEKEND, "23:00")): str,
                vol.Required(A_STAGGER_DELAY, default=current.get(A_STAGGER_DELAY, 10)): vol.All(int, vol.Range(min=0, max=300)),
            }
        
        schema = vol.Schema(schema_fields)
        
        if user_input is not None:
            # Validiere Zeitfelder (nur wenn vorhanden)
            errors = {}
            time_fields = [A_UP_TIME_WEEK, A_DOWN_TIME_WEEK, A_UP_TIME_WEEKEND, A_DOWN_TIME_WEEKEND, A_UP_EARLIEST, A_UP_LATEST]
            for field in time_fields:
                if field in user_input and user_input.get(field):
                    if not _validate_time(user_input.get(field)):
                        errors[field] = "Ungültiges Zeitformat (erwartet: HH:MM)"
            
            if errors:
                return self.async_show_form(step_id="edit_area_details", data_schema=schema, errors=errors)
            
            # Speichere Bereich mit allen Feldern
            area_data = {
                A_NAME: self._temp_area_data[A_NAME],
                A_MODE: mode,
                A_STAGGER_DELAY: user_input.get(A_STAGGER_DELAY, 10),
            }
            
            # Zeit-Felder (für TIME_ONLY, SUN, GOLDEN_HOUR)
            if mode in [MODE_TIME_ONLY, MODE_SUN, MODE_GOLDEN_HOUR]:
                area_data.update({
                    A_UP_TIME_WEEK: _validate_time(user_input.get(A_UP_TIME_WEEK, "07:00")),
                    A_DOWN_TIME_WEEK: _validate_time(user_input.get(A_DOWN_TIME_WEEK, "22:00")),
                    A_UP_TIME_WEEKEND: _validate_time(user_input.get(A_UP_TIME_WEEKEND, "08:00")),
                    A_DOWN_TIME_WEEKEND: _validate_time(user_input.get(A_DOWN_TIME_WEEKEND, "23:00")),
                })
            else:
                # Brightness: Behalte alte Werte
                area_data.update({
                    A_UP_TIME_WEEK: current.get(A_UP_TIME_WEEK, "07:00"),
                    A_DOWN_TIME_WEEK: current.get(A_DOWN_TIME_WEEK, "22:00"),
                    A_UP_TIME_WEEKEND: current.get(A_UP_TIME_WEEKEND, "08:00"),
                    A_DOWN_TIME_WEEKEND: current.get(A_DOWN_TIME_WEEKEND, "23:00"),
                })
            
            # Earliest/Latest (für SUN, GOLDEN_HOUR, BRIGHTNESS)
            if mode in [MODE_SUN, MODE_GOLDEN_HOUR, MODE_BRIGHTNESS]:
                area_data.update({
                    A_UP_EARLIEST: _validate_time(user_input.get(A_UP_EARLIEST, "06:00")),
                    A_UP_LATEST: _validate_time(user_input.get(A_UP_LATEST, "09:00")),
                })
            else:
                area_data.update({
                    A_UP_EARLIEST: current.get(A_UP_EARLIEST, "06:00"),
                    A_UP_LATEST: current.get(A_UP_LATEST, "09:00"),
                })
            
            # Helligkeits-Felder (nur für BRIGHTNESS)
            if mode == MODE_BRIGHTNESS:
                area_data.update({
                    A_BRIGHTNESS_SENSOR: _norm_empty(user_input.get(A_BRIGHTNESS_SENSOR)),
                    A_BRIGHTNESS_DOWN: user_input.get(A_BRIGHTNESS_DOWN, 5000),
                    A_BRIGHTNESS_UP: user_input.get(A_BRIGHTNESS_UP, 15000),
                })
            else:
                area_data.update({
                    A_BRIGHTNESS_SENSOR: current.get(A_BRIGHTNESS_SENSOR),
                    A_BRIGHTNESS_DOWN: current.get(A_BRIGHTNESS_DOWN, 5000),
                    A_BRIGHTNESS_UP: current.get(A_BRIGHTNESS_UP, 15000),
                })
            
            self._areas[self._edit_area] = area_data
            self._temp_area_data = {}  # Cleanup
            return await self.async_step_manage_areas()
        
        return self.async_show_form(step_id="edit_area_details", data_schema=schema)

    # ========== PROFIL-MANAGEMENT (ERWEITERT) ==========
    
    async def async_step_add_profile(self, user_input=None):
        """Profil hinzufügen mit allen neuen Feldern."""
        # Dynamisch alle Bereiche laden
        area_choices = {"none": "Keinem Bereich zuordnen"}
        for area_id, area_config in self._areas.items():
            area_name = area_config.get(A_NAME, area_id)
            area_choices[area_id] = area_name
        
        schema = vol.Schema({
            # Basis
            vol.Required(P_NAME): str,
            vol.Required(P_COVER): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="cover")
            ),
            vol.Optional(P_AREA, default="none"): vol.In(area_choices),
            
            # Sensoren
            vol.Optional(P_WINDOW): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor")
            ),
            vol.Optional(P_DOOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor")
            ),
            vol.Optional(P_LUX): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="illuminance")
            ),
            vol.Optional(P_TEMP): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
            ),
            
            # Positionen
            vol.Required(P_DAY_POS, default=40): vol.All(int, vol.Range(min=0, max=100)),
            vol.Required(P_NIGHT_POS, default=0): vol.All(int, vol.Range(min=0, max=100)),
            vol.Required(P_VPOS, default=self._base_opts.get(CONF_DEFAULT_VPOS, 30)): vol.All(int, vol.Range(min=0, max=80)),
            vol.Required(P_DOOR_SAFE, default=30): vol.All(int, vol.Range(min=0, max=80)),
            
            # Schwellwerte & Hysterese
            vol.Optional(P_LUX_TH, default=20000): vol.Coerce(float),
            vol.Optional(P_LUX_HYSTERESIS, default=20): vol.All(int, vol.Range(min=0, max=100)),
            vol.Optional(P_TEMP_TH, default=26): vol.Coerce(float),
            vol.Optional(P_TEMP_HYSTERESIS, default=10): vol.All(int, vol.Range(min=0, max=100)),
            
            # Sonnenposition
            vol.Optional(P_AZ_MIN, default=-360): vol.Coerce(float),
            vol.Optional(P_AZ_MAX, default=360): vol.Coerce(float),
            
            # Zeiten (überschreibt Bereich)
            vol.Optional(P_UP_TIME, default=""): str,
            vol.Optional(P_DOWN_TIME, default=""): str,
            
            # Erweiterte Features
            vol.Optional(P_WINDOW_OPEN_DELAY, default=0): vol.All(int, vol.Range(min=0, max=300)),
            vol.Optional(P_WINDOW_CLOSE_DELAY, default=0): vol.All(int, vol.Range(min=0, max=300)),
            vol.Optional(P_INTERMEDIATE_POS, default=0): vol.All(int, vol.Range(min=0, max=100)),
            vol.Optional(P_INTERMEDIATE_TIME, default=""): str,
            vol.Optional(P_HEAT_PROTECTION, default=False): bool,
            vol.Optional(P_HEAT_PROTECTION_TEMP, default=30): vol.Coerce(float),
            vol.Optional(P_KEEP_SUNPROTECT, default=False): bool,
            vol.Optional(P_BRIGHTNESS_END_DELAY, default=0): vol.All(int, vol.Range(min=0, max=60)),
            vol.Optional(P_NO_CLOSE_SUMMER, default=False): bool,
            
            # Cooldown & Status
            vol.Optional(P_COOLDOWN, default=self._base_opts.get(CONF_DEFAULT_COOLDOWN, 120)): vol.All(int, vol.Range(min=0, max=1800)),
            vol.Optional(P_ENABLED, default=True): bool,
            
            # Licht-Automation
            vol.Optional(P_LIGHT_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="light")
            ),
            vol.Optional(P_LIGHT_BRIGHTNESS, default=80): vol.All(int, vol.Range(min=0, max=100)),
            vol.Optional(P_LIGHT_ON_SHADE, default=True): bool,
            vol.Optional(P_LIGHT_ON_NIGHT, default=True): bool,
        })
        
        if user_input is not None:
            prof = dict(user_input)
            # Normalisiere leere Felder
            for k in (P_WINDOW, P_DOOR, P_LUX, P_TEMP, P_LIGHT_ENTITY):
                prof[k] = _norm_empty(prof.get(k))
            # Validiere Zeitfelder
            for k in (P_UP_TIME, P_DOWN_TIME, P_INTERMEDIATE_TIME):
                val = prof.get(k)
                if val:
                    normalized = _validate_time(val)
                    if normalized is None:
                        return self.async_show_form(
                            step_id="add_profile",
                            data_schema=schema,
                            errors={k: "Ungültiges Zeitformat (erwartet: HH:MM)"}
                        )
                    prof[k] = normalized
                else:
                    prof[k] = None
            self._profiles.append(prof)
            return await self.async_step_init()
        
        return self.async_show_form(step_id="add_profile", data_schema=schema)

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

        # Dynamisch alle Bereiche laden
        area_choices = {"none": "Keinem Bereich zuordnen"}
        for area_id, area_config in self._areas.items():
            area_name = area_config.get(A_NAME, area_id)
            area_choices[area_id] = area_name

        schema = vol.Schema({
            # Basis
            vol.Required(P_NAME, default=cur.get(P_NAME, "")): str,
            vol.Required(P_COVER, default=cur.get(P_COVER, "")): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="cover")
            ),
            vol.Optional(P_AREA, default=cur.get(P_AREA, "none")): vol.In(area_choices),
            
            # Sensoren
            vol.Optional(P_WINDOW, default=cur.get(P_WINDOW)): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor")
            ),
            vol.Optional(P_DOOR, default=cur.get(P_DOOR)): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor")
            ),
            vol.Optional(P_LUX, default=cur.get(P_LUX)): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="illuminance")
            ),
            vol.Optional(P_TEMP, default=cur.get(P_TEMP)): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
            ),
            
            # Positionen
            vol.Required(P_DAY_POS, default=cur.get(P_DAY_POS, 40)): vol.All(int, vol.Range(min=0, max=100)),
            vol.Required(P_NIGHT_POS, default=cur.get(P_NIGHT_POS, 0)): vol.All(int, vol.Range(min=0, max=100)),
            vol.Required(P_VPOS, default=cur.get(P_VPOS, self._base_opts.get(CONF_DEFAULT_VPOS, 30))): vol.All(int, vol.Range(min=0, max=80)),
            vol.Required(P_DOOR_SAFE, default=cur.get(P_DOOR_SAFE, 30)): vol.All(int, vol.Range(min=0, max=80)),
            
            # Schwellwerte & Hysterese
            vol.Optional(P_LUX_TH, default=cur.get(P_LUX_TH, 20000)): vol.Coerce(float),
            vol.Optional(P_LUX_HYSTERESIS, default=cur.get(P_LUX_HYSTERESIS, 20)): vol.All(int, vol.Range(min=0, max=100)),
            vol.Optional(P_TEMP_TH, default=cur.get(P_TEMP_TH, 26)): vol.Coerce(float),
            vol.Optional(P_TEMP_HYSTERESIS, default=cur.get(P_TEMP_HYSTERESIS, 10)): vol.All(int, vol.Range(min=0, max=100)),
            
            # Sonnenposition
            vol.Optional(P_AZ_MIN, default=cur.get(P_AZ_MIN, -360)): vol.Coerce(float),
            vol.Optional(P_AZ_MAX, default=cur.get(P_AZ_MAX, 360)): vol.Coerce(float),
            
            # Zeiten
            vol.Optional(P_UP_TIME, default=cur.get(P_UP_TIME) or ""): str,
            vol.Optional(P_DOWN_TIME, default=cur.get(P_DOWN_TIME) or ""): str,
            
            # Erweiterte Features
            vol.Optional(P_WINDOW_OPEN_DELAY, default=cur.get(P_WINDOW_OPEN_DELAY, 0)): vol.All(int, vol.Range(min=0, max=300)),
            vol.Optional(P_WINDOW_CLOSE_DELAY, default=cur.get(P_WINDOW_CLOSE_DELAY, 0)): vol.All(int, vol.Range(min=0, max=300)),
            vol.Optional(P_INTERMEDIATE_POS, default=cur.get(P_INTERMEDIATE_POS, 0)): vol.All(int, vol.Range(min=0, max=100)),
            vol.Optional(P_INTERMEDIATE_TIME, default=cur.get(P_INTERMEDIATE_TIME) or ""): str,
            vol.Optional(P_HEAT_PROTECTION, default=bool(cur.get(P_HEAT_PROTECTION, False))): bool,
            vol.Optional(P_HEAT_PROTECTION_TEMP, default=cur.get(P_HEAT_PROTECTION_TEMP, 30)): vol.Coerce(float),
            vol.Optional(P_KEEP_SUNPROTECT, default=bool(cur.get(P_KEEP_SUNPROTECT, False))): bool,
            vol.Optional(P_BRIGHTNESS_END_DELAY, default=cur.get(P_BRIGHTNESS_END_DELAY, 0)): vol.All(int, vol.Range(min=0, max=60)),
            vol.Optional(P_NO_CLOSE_SUMMER, default=bool(cur.get(P_NO_CLOSE_SUMMER, False))): bool,
            
            # Cooldown & Status
            vol.Optional(P_COOLDOWN, default=cur.get(P_COOLDOWN, self._base_opts.get(CONF_DEFAULT_COOLDOWN, 120))): vol.All(int, vol.Range(min=0, max=1800)),
            vol.Optional(P_ENABLED, default=bool(cur.get(P_ENABLED, True))): bool,
            
            # Licht-Automation
            vol.Optional(P_LIGHT_ENTITY, default=cur.get(P_LIGHT_ENTITY)): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="light")
            ),
            vol.Optional(P_LIGHT_BRIGHTNESS, default=cur.get(P_LIGHT_BRIGHTNESS, 80)): vol.All(int, vol.Range(min=0, max=100)),
            vol.Optional(P_LIGHT_ON_SHADE, default=bool(cur.get(P_LIGHT_ON_SHADE, True))): bool,
            vol.Optional(P_LIGHT_ON_NIGHT, default=bool(cur.get(P_LIGHT_ON_NIGHT, True))): bool,
        })
        
        if user_input is not None:
            newp = dict(user_input)
            # Normalisiere leere Felder
            for k in (P_WINDOW, P_DOOR, P_LUX, P_TEMP, P_LIGHT_ENTITY):
                newp[k] = _norm_empty(newp.get(k))
            # Validiere Zeitfelder
            for k in (P_UP_TIME, P_DOWN_TIME, P_INTERMEDIATE_TIME):
                val = newp.get(k)
                if val:
                    normalized = _validate_time(val)
                    if normalized is None:
                        return self.async_show_form(
                            step_id="edit_profile_form",
                            data_schema=schema,
                            errors={k: "Ungültiges Zeitformat (erwartet: HH:MM)"}
                        )
                    newp[k] = normalized
                else:
                    newp[k] = None
            self._profiles[idx] = newp
            return await self.async_step_init()
        
        return self.async_show_form(step_id="edit_profile_form", data_schema=schema)
