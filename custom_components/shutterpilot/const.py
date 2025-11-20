DOMAIN = "shutterpilot"

# Global config/options
CONF_GLOBAL_AUTO = "global_auto"
CONF_DEFAULT_VPOS = "default_ventilation_position"
CONF_DEFAULT_COOLDOWN = "default_cooldown"

# Areas (Bereiche) - Zeit-Templates
CONF_AREAS = "areas"
# Vordefinierte Standard-Bereiche (werden bei Setup angelegt)
AREA_LIVING = "living"
AREA_SLEEPING = "sleeping"
AREA_CHILDREN = "children"
DEFAULT_AREAS = [AREA_LIVING, AREA_SLEEPING, AREA_CHILDREN]

# Area configuration keys
A_NAME = "area_name"
A_UP_TIME_WEEK = "up_time_weekday"
A_DOWN_TIME_WEEK = "down_time_weekday"
A_UP_TIME_WEEKEND = "up_time_weekend"
A_DOWN_TIME_WEEKEND = "down_time_weekend"
A_UP_EARLIEST = "up_earliest"
A_UP_LATEST = "up_latest"
A_STAGGER_DELAY = "stagger_delay"
A_MODE = "area_mode"  # time_only, sun, golden_hour, brightness
A_BRIGHTNESS_SENSOR = "brightness_sensor"  # Helligkeitssensor für Bereich
A_BRIGHTNESS_DOWN = "brightness_down_lux"   # Lux-Wert zum Runterfahren
A_BRIGHTNESS_UP = "brightness_up_lux"       # Lux-Wert zum Hochfahren

# Area modes
MODE_TIME_ONLY = "time_only"
MODE_SUN = "sun"
MODE_GOLDEN_HOUR = "golden_hour"
MODE_BRIGHTNESS = "brightness"

# Profiles
CONF_PROFILES = "profiles"
P_NAME = "name"
P_COVER = "cover_entity_id"
P_AREA = "area"                # Bereichs-Zuordnung (living/sleeping/children/none)
P_WINDOW = "window_sensor"
P_DOOR = "door_sensor"
P_DAY_POS = "day_position"
P_NIGHT_POS = "night_position"
P_VPOS = "vent_position"
P_DOOR_SAFE = "door_safe_position"
P_LUX = "lux_sensor"
P_TEMP = "temp_sensor"
P_LUX_TH = "lux_threshold"
P_TEMP_TH = "temp_threshold"
P_LUX_HYSTERESIS = "lux_hysteresis"      # Hysterese in % für Helligkeitssensor
P_TEMP_HYSTERESIS = "temp_hysteresis"    # Hysterese in % für Temperatursensor
P_UP_TIME = "up_time"          # "HH:MM" or "" (überschreibt Bereich)
P_DOWN_TIME = "down_time"      # "HH:MM" or "" (überschreibt Bereich)
P_AZ_MIN = "azimuth_min"       # float deg
P_AZ_MAX = "azimuth_max"       # float deg
P_COOLDOWN = "cooldown_sec"    # int sec
P_ENABLED = "enabled"          # bool

# Erweiterte Features
P_WINDOW_OPEN_DELAY = "window_open_delay"    # Verzögerung beim Öffnen (Sekunden)
P_WINDOW_CLOSE_DELAY = "window_close_delay"  # Verzögerung beim Schließen (Sekunden)
P_INTERMEDIATE_POS = "intermediate_position"  # Zwischenposition (0-100)
P_INTERMEDIATE_TIME = "intermediate_time"     # Zeit für Zwischenposition "HH:MM"
P_HEAT_PROTECTION = "heat_protection_enabled" # Wärmeschutz aktiviert
P_HEAT_PROTECTION_TEMP = "heat_protection_temp" # Temperatur für vollständiges Schließen
P_KEEP_SUNPROTECT = "keep_in_sunprotect"     # Im Sonnenschutz halten
P_BRIGHTNESS_END_DELAY = "brightness_end_delay" # Verzögerung für Helligkeits-Unterschreitung (Min)
P_NO_CLOSE_SUMMER = "no_close_in_summer"     # Im Sommer nicht schließen

# Light automation
P_LIGHT_ENTITY = "light_entity"           # light.xyz entity
P_LIGHT_BRIGHTNESS = "light_brightness"   # 0-100%
P_LIGHT_ON_SHADE = "light_on_shade"       # bool: Licht bei Beschattung an
P_LIGHT_ON_NIGHT = "light_on_night"       # bool: Licht bei Nacht an

# Summer period (global)
CONF_SUMMER_START = "summer_start"        # MM-DD
CONF_SUMMER_END = "summer_end"            # MM-DD

# Global astro settings
CONF_SUN_ELEVATION_END = "sun_elevation_end"  # Elevation zum Beenden des Sonnenschutzes
CONF_SUN_OFFSET_UP = "sun_offset_up"          # Offset in Minuten fürs Hochfahren
CONF_SUN_OFFSET_DOWN = "sun_offset_down"      # Offset in Minuten fürs Runterfahren

# Runtime keys
DATA = "data"
RUNTIME_PROFILES = "runtime_profiles"
RUNTIME_AREAS = "runtime_areas"
UNSUBS = "unsubs"
