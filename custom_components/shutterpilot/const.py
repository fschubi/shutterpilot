DOMAIN = "shutterpilot"

# Global config/options
CONF_GLOBAL_AUTO = "global_auto"
CONF_DEFAULT_VPOS = "default_ventilation_position"
CONF_DEFAULT_COOLDOWN = "default_cooldown"

# Profiles
CONF_PROFILES = "profiles"
P_NAME = "name"
P_COVER = "cover_entity_id"
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
P_UP_TIME = "up_time"          # "HH:MM" or ""
P_DOWN_TIME = "down_time"      # "HH:MM" or ""
P_AZ_MIN = "azimuth_min"       # float deg
P_AZ_MAX = "azimuth_max"       # float deg
P_COOLDOWN = "cooldown_sec"    # int sec
P_ENABLED = "enabled"          # bool

# Light automation
P_LIGHT_ENTITY = "light_entity"           # light.xyz entity
P_LIGHT_BRIGHTNESS = "light_brightness"   # 0-100%
P_LIGHT_ON_SHADE = "light_on_shade"       # bool: Licht bei Beschattung an
P_LIGHT_ON_NIGHT = "light_on_night"       # bool: Licht bei Nacht an

# Runtime keys
DATA = "data"
RUNTIME_PROFILES = "runtime_profiles"
UNSUBS = "unsubs"
