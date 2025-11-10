/**
 * ShutterPilot Management Card
 * Professional Enterprise-Level UI for ShutterPilot
 * Version: 2.2.1 - Fixed Save to Backend
 */

class ShutterPilotCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._hass = null;
    this._config = null;
    this._configEntry = null;
    this._profiles = [];
    this._areas = {};
    this._globalSettings = {};
    this._editingProfile = null;
    this._editingArea = null;
    this._editDialogTab = 'basic';
    this._activeTab = 'profiles';
    this._selectedProfiles = new Set();
    this._tempProfileData = null;  // Zwischenspeicher für Profil-Bearbeitung
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('Bitte definiere eine Entity (switch.shutterpilot_global_automation)');
    }
    this._config = config;
  }

  set hass(hass) {
    const oldHass = this._hass;
    this._hass = hass;
    
    if (!oldHass || this._needsUpdate(oldHass, hass)) {
      this._loadConfigEntry();
    }
    
    this.render();
  }

  _needsUpdate(oldHass, newHass) {
    const oldGlobal = oldHass?.states[this._config.entity];
    const newGlobal = newHass?.states[this._config.entity];
    
    if (oldGlobal?.state !== newGlobal?.state) return true;
    
    const oldSwitches = Object.keys(oldHass?.states || {}).filter(e => e.startsWith('switch.shutterpilot_'));
    const newSwitches = Object.keys(newHass?.states || {}).filter(e => e.startsWith('switch.shutterpilot_'));
    
    if (oldSwitches.length !== newSwitches.length) return true;
    
    return false;
  }

  async _loadConfigEntry() {
    if (!this._hass) return;

    try {
      // Find config sensor with explicit entity_id
      const configSensorId = 'sensor.shutterpilot_config';
      const sensorState = this._hass.states[configSensorId];

      if (!sensorState) {
        console.warn('❌ ShutterPilot Config Sensor nicht gefunden:', configSensorId);
        console.warn('Verfügbare Sensoren:', Object.keys(this._hass.states).filter(e => e.includes('shutterpilot')));
        return;
      }

      if (!sensorState.attributes) {
        console.warn('❌ Config Sensor hat keine Attributes');
        return;
      }

      const attrs = sensorState.attributes;
      console.log('✅ Config Sensor geladen:', attrs);
      
      // Store entry ID
      this._configEntry = {
        entry_id: attrs.entry_id,
        options: {
          profiles: attrs.profiles || [],
          areas: attrs.areas || {},
          ...attrs.global_settings
        }
      };
      
      this._profiles = attrs.profiles || [];
      this._areas = attrs.areas || this._getDefaultAreas();
      this._globalSettings = attrs.global_settings || {
        default_vpos: 30,
        default_cooldown: 120,
        summer_start: '05-01',
        summer_end: '09-30',
        sun_elevation_end: 3.0,
        sun_offset_up: 0,
        sun_offset_down: 0,
      };

      console.log(`✅ ${this._profiles.length} Profile geladen:`, this._profiles.map(p => p.name));
      this._enrichProfilesWithStatus();

    } catch (err) {
      console.error('❌ Fehler beim Laden der Config Entry:', err);
    }
  }

  _getDefaultAreas() {
    return {
      living: {
        name: 'Wohnbereich',
        mode: 'sun',
        up_time_week: '06:30',
        down_time_week: '22:00',
        up_time_weekend: '08:00',
        down_time_weekend: '23:00',
        up_earliest: '06:00',
        up_latest: '09:00',
        stagger_delay: 10,
      },
      sleeping: {
        name: 'Schlafbereich',
        mode: 'time_only',
        up_time_week: '06:00',
        down_time_week: '22:30',
        up_time_weekend: '09:00',
        down_time_weekend: '23:30',
        up_earliest: '06:00',
        up_latest: '10:00',
        stagger_delay: 5,
      },
      children: {
        name: 'Kinderbereich',
        mode: 'sun',
        up_time_week: '06:45',
        down_time_week: '21:30',
        up_time_weekend: '08:30',
        down_time_weekend: '22:30',
        up_earliest: '06:30',
        up_latest: '09:00',
        stagger_delay: 8,
      },
    };
  }

  _enrichProfilesWithStatus() {
    if (!this._hass || !this._profiles) return;

    this._profiles = this._profiles.map(profile => {
      const sanitizedName = profile.name.toLowerCase().replace(/[^a-z0-9]/g, '_');
      
      const statusSensor = this._hass.states[`sensor.shutterpilot_${sanitizedName}_status`];
      const enabledSwitch = this._hass.states[`switch.shutterpilot_${sanitizedName}_automation`];
      
      return {
        ...profile,
        status: statusSensor?.state || 'unknown',
        enabled: enabledSwitch?.state === 'on',
        _entities: {
          status: statusSensor?.entity_id,
          switch: enabledSwitch?.entity_id,
        }
      };
    });
  }

  render() {
    if (!this._hass || !this._config) return;

    const tabContent = this._activeTab === 'profiles' ? this._renderProfilesTab() :
                       this._activeTab === 'areas' ? this._renderAreasTab() :
                       this._renderGlobalTab();

    this.shadowRoot.innerHTML = `
      <style>${this._getStyles()}</style>
      <div class="card-container">
        ${this._renderHeader()}
        ${this._renderTabs()}
        <div class="card-content">${tabContent}</div>
        ${this._editingProfile !== null ? this._renderProfileEditDialog() : ''}
        ${this._editingArea !== null ? this._renderAreaEditDialog() : ''}
      </div>
    `;

    this._attachEventListeners();
  }

  _renderHeader() {
    return `
      <div class="card-header">
        <div class="header-left">
          <ha-icon icon="mdi:window-shutter"></ha-icon>
          <h1>ShutterPilot</h1>
          <span class="subtitle">Enterprise Rollladensteuerung</span>
        </div>
        <div class="header-right">
          <button class="icon-button" data-action="refresh" title="Aktualisieren">
            <ha-icon icon="mdi:refresh"></ha-icon>
          </button>
        </div>
      </div>
    `;
  }

  _renderTabs() {
    return `
      <div class="tabs">
        <button class="tab ${this._activeTab === 'profiles' ? 'active' : ''}" 
                data-tab="profiles">
          <ha-icon icon="mdi:view-list"></ha-icon>
          Profile
        </button>
        <button class="tab ${this._activeTab === 'areas' ? 'active' : ''}" 
                data-tab="areas">
          <ha-icon icon="mdi:home-group"></ha-icon>
          Bereiche
        </button>
        <button class="tab ${this._activeTab === 'global' ? 'active' : ''}" 
                data-tab="global">
          <ha-icon icon="mdi:cog-outline"></ha-icon>
          Global
        </button>
      </div>
    `;
  }

  _renderProfilesTab() {
    if (!this._profiles || this._profiles.length === 0) {
      return `
        <div class="empty-state">
          <ha-icon icon="mdi:window-shutter-open"></ha-icon>
          <h3>Keine Profile vorhanden</h3>
          <p>Erstelle dein erstes Profil direkt hier in der Card</p>
          <button class="btn btn-primary" data-action="add-profile">
            <ha-icon icon="mdi:plus"></ha-icon>
            Neues Profil erstellen
          </button>
        </div>
      `;
    }

    return `
      <div class="toolbar">
        <button class="btn btn-primary" data-action="add-profile">
          <ha-icon icon="mdi:plus"></ha-icon>
          Neues Profil
        </button>
        <div class="toolbar-actions">
          <button class="btn btn-secondary" data-service="all_up">
            <ha-icon icon="mdi:arrow-up"></ha-icon>
            Alle hoch
          </button>
          <button class="btn btn-secondary" data-service="all_down">
            <ha-icon icon="mdi:arrow-down"></ha-icon>
            Alle runter
          </button>
          <button class="btn btn-secondary" data-service="stop">
            <ha-icon icon="mdi:stop"></ha-icon>
            Stopp
          </button>
        </div>
      </div>

      <div class="profile-table">
        <div class="table-header">
          <div class="th th-status">Status</div>
          <div class="th th-name">Name</div>
          <div class="th th-cover">Rollladen</div>
          <div class="th th-area">Bereich</div>
          <div class="th th-sensors">Sensoren</div>
          <div class="th th-actions">Aktionen</div>
        </div>

        ${this._profiles.map((profile, idx) => this._renderProfileRow(profile, idx)).join('')}
      </div>
    `;
  }

  _renderProfileRow(profile, index) {
    const areaName = profile.area ? (this._areas[profile.area]?.name || 'Unbekannt') : 'Kein Bereich';
    const statusClass = this._getStatusClass(profile.status);
    const statusText = this._getStatusText(profile.status);
    
    return `
      <div class="table-row ${profile.enabled ? '' : 'disabled'}">
        <div class="td td-status">
          <span class="status-badge status-${statusClass}">
            ${statusText}
          </span>
        </div>
        <div class="td td-name">
          <strong>${profile.name}</strong>
          ${!profile.enabled ? '<span class="disabled-label">(Deaktiviert)</span>' : ''}
        </div>
        <div class="td td-cover">
          <code>${profile.cover || 'N/A'}</code>
        </div>
        <div class="td td-area">
          <span class="area-badge">${areaName}</span>
        </div>
        <div class="td td-sensors">
          <div class="sensor-icons">
            ${profile.window_sensor ? '<ha-icon icon="mdi:window-open" title="Fenster"></ha-icon>' : ''}
            ${profile.door_sensor ? '<ha-icon icon="mdi:door-open" title="Tür"></ha-icon>' : ''}
            ${profile.lux_sensor ? '<ha-icon icon="mdi:brightness-5" title="Helligkeit"></ha-icon>' : ''}
            ${profile.temp_sensor ? '<ha-icon icon="mdi:thermometer" title="Temperatur"></ha-icon>' : ''}
            ${!profile.window_sensor && !profile.door_sensor && !profile.lux_sensor && !profile.temp_sensor ? 
              '<span class="no-sensors">Keine</span>' : ''}
          </div>
        </div>
        <div class="td td-actions">
          <button class="action-btn" data-action="toggle" data-index="${index}" 
                  title="${profile.enabled ? 'Deaktivieren' : 'Aktivieren'}">
            <ha-icon icon="${profile.enabled ? 'mdi:pause' : 'mdi:play'}"></ha-icon>
          </button>
          <button class="action-btn" data-action="edit" data-index="${index}" title="Bearbeiten">
            <ha-icon icon="mdi:pencil"></ha-icon>
          </button>
          <button class="action-btn" data-action="copy" data-index="${index}" title="Duplizieren">
            <ha-icon icon="mdi:content-copy"></ha-icon>
          </button>
          <button class="action-btn action-delete" data-action="delete" data-index="${index}" title="Löschen">
            <ha-icon icon="mdi:delete"></ha-icon>
          </button>
        </div>
      </div>
    `;
  }

  _renderAreasTab() {
    const areas = Object.entries(this._areas);
    
    return `
      <div class="areas-grid">
        ${areas.map(([key, area]) => this._renderAreaCard(key, area)).join('')}
      </div>
    `;
  }

  _renderAreaCard(key, area) {
    const profileCount = this._profiles.filter(p => p.area === key).length;
    const modeText = this._getModeText(area.mode);

    return `
      <div class="area-card">
        <div class="area-header">
          <h3>${area.name}</h3>
          <button class="btn-icon" data-action="edit-area" data-area="${key}" title="Bearbeiten">
            <ha-icon icon="mdi:pencil"></ha-icon>
          </button>
        </div>
        <div class="area-info">
          <div class="info-row">
            <span class="label">Modus:</span>
            <span class="value">${modeText}</span>
          </div>
          <div class="info-row">
            <span class="label">Hochfahren (Woche):</span>
            <span class="value">${area.up_time_week || '-'}</span>
          </div>
          <div class="info-row">
            <span class="label">Runterfahren (Woche):</span>
            <span class="value">${area.down_time_week || '-'}</span>
          </div>
          <div class="info-row">
            <span class="label">Hochfahren (Wochenende):</span>
            <span class="value">${area.up_time_weekend || '-'}</span>
          </div>
          <div class="info-row">
            <span class="label">Runterfahren (Wochenende):</span>
            <span class="value">${area.down_time_weekend || '-'}</span>
          </div>
          <div class="info-row">
            <span class="label">Zugeordnete Profile:</span>
            <span class="value badge">${profileCount}</span>
          </div>
        </div>
      </div>
    `;
  }

  _renderGlobalTab() {
    const globalAuto = this._hass.states[this._config.entity];
    const isOn = globalAuto?.state === 'on';

    return `
      <div class="global-settings">
        <div class="setting-card">
          <div class="setting-header">
            <h3>Globale Automatik</h3>
            <label class="switch">
              <input type="checkbox" ${isOn ? 'checked' : ''} data-action="toggle-global">
              <span class="slider"></span>
            </label>
          </div>
          <p class="setting-description">
            ${isOn ? '✅ Automatische Steuerung ist aktiv' : '⚠️ Automatische Steuerung ist deaktiviert'}
          </p>
        </div>

        <div class="setting-card">
          <h3>Services</h3>
          <div class="service-buttons">
            <button class="btn btn-block btn-secondary" data-service="recalculate_now">
              <ha-icon icon="mdi:refresh"></ha-icon>
              Sofort neu berechnen
            </button>
          </div>
        </div>

        <div class="setting-card">
          <h3>Sommerzeitraum</h3>
          <div class="info-grid">
            <div class="info-item">
              <span class="label">Beginn:</span>
              <span class="value">${this._formatDate(this._globalSettings.summer_start)}</span>
            </div>
            <div class="info-item">
              <span class="label">Ende:</span>
              <span class="value">${this._formatDate(this._globalSettings.summer_end)}</span>
            </div>
          </div>
        </div>

        <div class="setting-card">
          <h3>Statistik</h3>
          <div class="info-grid">
            <div class="info-item">
              <span class="label">Anzahl Profile:</span>
              <span class="value badge">${this._profiles.length}</span>
            </div>
            <div class="info-item">
              <span class="label">Aktive Profile:</span>
              <span class="value badge">${this._profiles.filter(p => p.enabled).length}</span>
            </div>
            <div class="info-item">
              <span class="label">Bereiche:</span>
              <span class="value badge">${Object.keys(this._areas).length}</span>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  _renderProfileEditDialog() {
    // Verwende temporäre Daten falls vorhanden, sonst Original-Profil
    const originalProfile = this._editingProfile?.index >= 0 ? 
      this._profiles[this._editingProfile.index] : 
      this._getEmptyProfile();
    
    const profile = this._tempProfileData || originalProfile;
    
    const isNew = this._editingProfile?.index === -1;
    const title = isNew ? 'Neues Profil erstellen' : `Profil bearbeiten: ${profile.name}`;

    return `
      <div class="dialog-overlay">
        <div class="dialog">
          <div class="dialog-header">
            <h2>${title}</h2>
            <button class="btn-icon-dialog" data-action="close-dialog">
              <ha-icon icon="mdi:close"></ha-icon>
            </button>
          </div>

          <div class="dialog-tabs">
            <button class="dialog-tab ${this._editDialogTab === 'basic' ? 'active' : ''}" data-dialog-tab="basic">Basis</button>
            <button class="dialog-tab ${this._editDialogTab === 'sensors' ? 'active' : ''}" data-dialog-tab="sensors">Sensoren</button>
            <button class="dialog-tab ${this._editDialogTab === 'sun' ? 'active' : ''}" data-dialog-tab="sun">Sonnenschutz</button>
            <button class="dialog-tab ${this._editDialogTab === 'advanced' ? 'active' : ''}" data-dialog-tab="advanced">Erweitert</button>
          </div>

          <div class="dialog-content">
            <form id="profile-form">
              ${this._renderProfileEditForm(profile)}
            </form>
          </div>

          <div class="dialog-footer">
            <button class="btn btn-secondary" data-action="close-dialog">
              Abbrechen
            </button>
            <button class="btn btn-primary" data-action="save-profile">
              <ha-icon icon="mdi:content-save"></ha-icon>
              Speichern
            </button>
          </div>
        </div>
      </div>
    `;
  }

  _renderProfileEditForm(profile) {
    if (this._editDialogTab === 'basic') {
      return this._renderProfileBasicForm(profile);
    } else if (this._editDialogTab === 'sensors') {
      return this._renderProfileSensorsForm(profile);
    } else if (this._editDialogTab === 'sun') {
      return this._renderProfileSunForm(profile);
    } else {
      return this._renderProfileAdvancedForm(profile);
    }
  }

  _renderProfileBasicForm(profile) {
    const coverEntities = Object.keys(this._hass.states).filter(e => e.startsWith('cover.'));
    const areas = Object.entries(this._areas);

    return `
      <div class="form-group">
        <label>Profilname *</label>
        <input type="text" name="name" value="${profile.name || ''}" required class="form-input">
      </div>

      <div class="form-group">
        <label>Cover Entity *</label>
        <select name="cover" required class="form-input">
          <option value="">-- Bitte wählen --</option>
          ${coverEntities.map(e => `
            <option value="${e}" ${profile.cover === e ? 'selected' : ''}>${e}</option>
          `).join('')}
        </select>
      </div>

      <div class="form-group">
        <label>Bereich zuordnen</label>
        <select name="area" class="form-input">
          <option value="">Keinem Bereich</option>
          ${areas.map(([key, area]) => `
            <option value="${key}" ${profile.area === key ? 'selected' : ''}>${area.name}</option>
          `).join('')}
        </select>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label>Tagesposition (%)</label>
          <input type="number" name="day_pos" value="${profile.day_pos || 40}" min="0" max="100" class="form-input">
        </div>
        <div class="form-group">
          <label>Nachtposition (%)</label>
          <input type="number" name="night_pos" value="${profile.night_pos || 0}" min="0" max="100" class="form-input">
        </div>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label>Lüftungsposition (%)</label>
          <input type="number" name="vent_pos" value="${profile.vent_pos || 30}" min="0" max="80" class="form-input">
        </div>
        <div class="form-group">
          <label>Tür-Position (%)</label>
          <input type="number" name="door_safe" value="${profile.door_safe || 30}" min="0" max="80" class="form-input">
        </div>
      </div>

      <div class="form-group">
        <label>Cooldown (Sekunden)</label>
        <input type="number" name="cooldown" value="${profile.cooldown || 120}" min="0" max="1800" class="form-input">
      </div>

      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" name="enabled" ${profile.enabled !== false ? 'checked' : ''}>
          <span>Profil aktiviert</span>
        </label>
      </div>
    `;
  }

  _renderProfileSensorsForm(profile) {
    const binarySensors = Object.keys(this._hass.states).filter(e => e.startsWith('binary_sensor.'));
    const luxSensors = Object.keys(this._hass.states).filter(e => 
      e.startsWith('sensor.') && (e.includes('lux') || e.includes('bright') || e.includes('illuminance'))
    );
    const tempSensors = Object.keys(this._hass.states).filter(e => 
      e.startsWith('sensor.') && (e.includes('temp') || e.includes('temperature'))
    );

    return `
      <div class="form-group highlight-sensor">
        <label>
          <ha-icon icon="mdi:brightness-5"></ha-icon>
          Helligkeitssensor (Lux) - Wichtig für Beschattung!
        </label>
        <select name="lux_sensor" class="form-input">
          <option value="">Kein Sensor</option>
          ${luxSensors.map(e => `
            <option value="${e}" ${profile.lux_sensor === e ? 'selected' : ''}>${e}</option>
          `).join('')}
        </select>
        <small class="form-hint">
          ${profile.lux_sensor ? '✅ Sensor konfiguriert' : '⚠️ Empfohlen für automatische Beschattung'}
        </small>
      </div>

      <div class="form-group">
        <label>
          <ha-icon icon="mdi:window-open"></ha-icon>
          Fenster-Sensor
        </label>
        <select name="window_sensor" class="form-input">
          <option value="">Kein Sensor</option>
          ${binarySensors.map(e => `
            <option value="${e}" ${profile.window_sensor === e ? 'selected' : ''}>${e}</option>
          `).join('')}
        </select>
      </div>

      <div class="form-group">
        <label>
          <ha-icon icon="mdi:door-open"></ha-icon>
          Tür-Sensor
        </label>
        <select name="door_sensor" class="form-input">
          <option value="">Kein Sensor</option>
          ${binarySensors.map(e => `
            <option value="${e}" ${profile.door_sensor === e ? 'selected' : ''}>${e}</option>
          `).join('')}
        </select>
      </div>

      <div class="form-group">
        <label>
          <ha-icon icon="mdi:thermometer"></ha-icon>
          Temperatur-Sensor
        </label>
        <select name="temp_sensor" class="form-input">
          <option value="">Kein Sensor</option>
          ${tempSensors.map(e => `
            <option value="${e}" ${profile.temp_sensor === e ? 'selected' : ''}>${e}</option>
          `).join('')}
        </select>
      </div>
    `;
  }

  _renderProfileSunForm(profile) {
    return `
      <div class="form-row">
        <div class="form-group">
          <label>Helligkeits-Schwellwert (lx)</label>
          <input type="number" name="lux_th" value="${profile.lux_th || 20000}" min="0" class="form-input">
        </div>
        <div class="form-group">
          <label>Helligkeits-Hysterese (%)</label>
          <input type="number" name="lux_hysteresis" value="${profile.lux_hysteresis || 20}" min="0" max="100" class="form-input">
        </div>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label>Temperatur-Schwellwert (°C)</label>
          <input type="number" name="temp_th" value="${profile.temp_th || 26}" min="0" step="0.1" class="form-input">
        </div>
        <div class="form-group">
          <label>Temperatur-Hysterese (%)</label>
          <input type="number" name="temp_hysteresis" value="${profile.temp_hysteresis || 10}" min="0" max="100" class="form-input">
        </div>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label>Azimut Min (°)</label>
          <input type="number" name="az_min" value="${profile.az_min || -360}" min="-360" max="360" class="form-input">
        </div>
        <div class="form-group">
          <label>Azimut Max (°)</label>
          <input type="number" name="az_max" value="${profile.az_max || 360}" min="-360" max="360" class="form-input">
        </div>
      </div>

      <div class="form-group">
        <label>Beschattungsposition (%)</label>
        <input type="number" name="shade_pos" value="${profile.shade_pos || 20}" min="0" max="100" class="form-input">
      </div>

      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" name="keep_sunprotect" ${profile.keep_sunprotect ? 'checked' : ''}>
          <span>Im Sonnenschutz halten</span>
        </label>
      </div>
    `;
  }

  _renderProfileAdvancedForm(profile) {
    return `
      <div class="form-row">
        <div class="form-group">
          <label>Fenster öffnen Verzögerung (s)</label>
          <input type="number" name="window_open_delay" value="${profile.window_open_delay || 0}" min="0" max="300" class="form-input">
        </div>
        <div class="form-group">
          <label>Fenster schließen Verzögerung (s)</label>
          <input type="number" name="window_close_delay" value="${profile.window_close_delay || 0}" min="0" max="300" class="form-input">
        </div>
      </div>

      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" name="heat_protection" ${profile.heat_protection ? 'checked' : ''}>
          <span>Wärmeschutz aktivieren</span>
        </label>
      </div>

      <div class="form-group">
        <label>Wärmeschutz-Temperatur (°C)</label>
        <input type="number" name="heat_protection_temp" value="${profile.heat_protection_temp || 30}" min="0" step="0.1" class="form-input">
      </div>

      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" name="no_close_summer" ${profile.no_close_summer ? 'checked' : ''}>
          <span>Im Sommer nicht schließen</span>
        </label>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label>Zwischenposition (%)</label>
          <input type="number" name="intermediate_pos" value="${profile.intermediate_pos || 0}" min="0" max="100" class="form-input">
        </div>
        <div class="form-group">
          <label>Zwischenzeit (HH:MM)</label>
          <input type="time" name="intermediate_time" value="${profile.intermediate_time || ''}" class="form-input">
        </div>
      </div>

      <div class="form-group">
        <label>Helligkeits-Ende Verzögerung (min)</label>
        <input type="number" name="brightness_end_delay" value="${profile.brightness_end_delay || 0}" min="0" max="60" class="form-input">
      </div>
    `;
  }

  _renderAreaEditDialog() {
    const areaKey = this._editingArea;
    const area = this._areas[areaKey] || {};
    const areaNames = {
      living: 'Wohnbereich',
      sleeping: 'Schlafbereich',
      children: 'Kinderbereich'
    };

    return `
      <div class="dialog-overlay">
        <div class="dialog">
          <div class="dialog-header">
            <h2>Bereich bearbeiten: ${area.name || areaNames[areaKey]}</h2>
            <button class="btn-icon-dialog" data-action="close-dialog">
              <ha-icon icon="mdi:close"></ha-icon>
            </button>
          </div>

          <div class="dialog-content">
            <form id="area-form">
              <div class="form-group">
                <label>Name</label>
                <input type="text" name="name" value="${area.name || ''}" required class="form-input">
              </div>

              <div class="form-group">
                <label>Modus</label>
                <select name="mode" class="form-input">
                  <option value="time_only" ${area.mode === 'time_only' ? 'selected' : ''}>Nur Zeit</option>
                  <option value="sun" ${area.mode === 'sun' ? 'selected' : ''}>Sonnenstand</option>
                  <option value="golden_hour" ${area.mode === 'golden_hour' ? 'selected' : ''}>Golden Hour</option>
                  <option value="brightness" ${area.mode === 'brightness' ? 'selected' : ''}>Helligkeitssensor</option>
                </select>
              </div>

              <h4 class="form-section-title">Wochentag</h4>
              <div class="form-row">
                <div class="form-group">
                  <label>Hochfahrzeit</label>
                  <input type="time" name="up_time_week" value="${area.up_time_week || ''}" class="form-input">
                </div>
                <div class="form-group">
                  <label>Runterfahrzeit</label>
                  <input type="time" name="down_time_week" value="${area.down_time_week || ''}" class="form-input">
                </div>
              </div>

              <h4 class="form-section-title">Wochenende</h4>
              <div class="form-row">
                <div class="form-group">
                  <label>Hochfahrzeit</label>
                  <input type="time" name="up_time_weekend" value="${area.up_time_weekend || ''}" class="form-input">
                </div>
                <div class="form-group">
                  <label>Runterfahrzeit</label>
                  <input type="time" name="down_time_weekend" value="${area.down_time_weekend || ''}" class="form-input">
                </div>
              </div>

              <h4 class="form-section-title">Grenzen</h4>
              <div class="form-row">
                <div class="form-group">
                  <label>Früheste Hochfahrzeit</label>
                  <input type="time" name="up_earliest" value="${area.up_earliest || ''}" class="form-input">
                </div>
                <div class="form-group">
                  <label>Späteste Hochfahrzeit</label>
                  <input type="time" name="up_latest" value="${area.up_latest || ''}" class="form-input">
                </div>
              </div>

              <div class="form-group">
                <label>Verzögerung (Sekunden)</label>
                <input type="number" name="stagger_delay" value="${area.stagger_delay || 0}" min="0" max="300" class="form-input">
              </div>
            </form>
          </div>

          <div class="dialog-footer">
            <button class="btn btn-secondary" data-action="close-dialog">
              Abbrechen
            </button>
            <button class="btn btn-primary" data-action="save-area">
              <ha-icon icon="mdi:content-save"></ha-icon>
              Speichern
            </button>
          </div>
        </div>
      </div>
    `;
  }

  _getEmptyProfile() {
    return {
      name: '',
      cover: '',
      area: '',
      day_pos: 40,
      night_pos: 0,
      vent_pos: 30,
      door_safe: 30,
      cooldown: 120,
      enabled: true,
      window_sensor: '',
      door_sensor: '',
      lux_sensor: '',
      temp_sensor: '',
      lux_th: 20000,
      lux_hysteresis: 20,
      temp_th: 26,
      temp_hysteresis: 10,
      az_min: -360,
      az_max: 360,
      shade_pos: 20,
      window_open_delay: 0,
      window_close_delay: 0,
      heat_protection: false,
      heat_protection_temp: 30,
      no_close_summer: false,
      intermediate_pos: 0,
      intermediate_time: '',
      brightness_end_delay: 0,
      keep_sunprotect: false,
    };
  }

  // Event Listeners
  _attachEventListeners() {
    const root = this.shadowRoot;

    // Header Buttons
    root.querySelectorAll('[data-action="refresh"]').forEach(btn => {
      btn.addEventListener('click', () => this._refresh());
    });

    // Tab Navigation
    root.querySelectorAll('[data-tab]').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const tabName = e.currentTarget.getAttribute('data-tab');
        this._setTab(tabName);
      });
    });

    // Service Buttons
    root.querySelectorAll('[data-service]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const service = e.currentTarget.getAttribute('data-service');
        this._callService(service);
      });
    });

    // Profile Actions
    root.querySelectorAll('[data-action="add-profile"]').forEach(btn => {
      btn.addEventListener('click', () => this._addProfile());
    });

    root.querySelectorAll('[data-action="toggle"]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const index = parseInt(e.currentTarget.getAttribute('data-index'));
        this._toggleProfileEnabled(index);
      });
    });

    root.querySelectorAll('[data-action="edit"]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const index = parseInt(e.currentTarget.getAttribute('data-index'));
        this._editProfile(index);
      });
    });

    root.querySelectorAll('[data-action="copy"]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const index = parseInt(e.currentTarget.getAttribute('data-index'));
        this._copyProfile(index);
      });
    });

    root.querySelectorAll('[data-action="delete"]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const index = parseInt(e.currentTarget.getAttribute('data-index'));
        this._deleteProfile(index);
      });
    });

    // Area Actions
    root.querySelectorAll('[data-action="edit-area"]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const area = e.currentTarget.getAttribute('data-area');
        this._editArea(area);
      });
    });

    // Global Auto Toggle
    root.querySelectorAll('[data-action="toggle-global"]').forEach(cb => {
      cb.addEventListener('change', (e) => {
        this._toggleGlobalAuto(e.target.checked);
      });
    });

    // Dialog Actions
    root.querySelectorAll('[data-action="close-dialog"]').forEach(btn => {
      btn.addEventListener('click', () => this._closeDialog());
    });

    root.querySelectorAll('[data-dialog-tab]').forEach(tab => {
      tab.addEventListener('click', (e) => {
        // Speichere aktuelle Formular-Daten vor Tab-Wechsel
        this._saveCurrentProfileFormData();
        
        this._editDialogTab = e.currentTarget.getAttribute('data-dialog-tab');
        this.render();
      });
    });

    root.querySelectorAll('[data-action="save-profile"]').forEach(btn => {
      btn.addEventListener('click', () => this._saveProfile());
    });

    root.querySelectorAll('[data-action="save-area"]').forEach(btn => {
      btn.addEventListener('click', () => this._saveArea());
    });
  }

  _setTab(tab) {
    this._activeTab = tab;
    this.render();
  }

  async _refresh() {
    await this._loadConfigEntry();
    this.render();
    this._showToast('Daten aktualisiert');
  }

  _addProfile() {
    this._editingProfile = { index: -1 };
    this._editDialogTab = 'basic';
    this._tempProfileData = null;  // Reset temporäre Daten
    this.render();
  }

  _editProfile(index) {
    this._editingProfile = { index };
    this._editDialogTab = 'basic';
    this._tempProfileData = null;  // Reset temporäre Daten
    this.render();
  }

  async _copyProfile(index) {
    const profile = { ...this._profiles[index] };
    profile.name = `${profile.name} (Kopie)`;
    delete profile.status;
    delete profile.enabled;
    delete profile._entities;

    this._profiles.push(profile);
    await this._saveConfig();
    this._showToast('Profil dupliziert');
  }

  async _deleteProfile(index) {
    const profile = this._profiles[index];
    if (!confirm(`Profil "${profile.name}" wirklich löschen?`)) return;

    this._profiles.splice(index, 1);
    await this._saveConfig();
    this._showToast('Profil gelöscht');
  }

  _editArea(areaKey) {
    this._editingArea = areaKey;
    this.render();
  }

  _saveCurrentProfileFormData() {
    // Sammle aktuelle Formular-Daten aus dem Dialog
    const form = this.shadowRoot.querySelector('#profile-form');
    if (!form) return;
    
    const formData = new FormData(form);
    
    // Initialisiere temporäre Daten mit aktuellem Profil falls noch nicht vorhanden
    if (!this._tempProfileData) {
      const originalProfile = this._editingProfile?.index >= 0 ? 
        this._profiles[this._editingProfile.index] : 
        this._getEmptyProfile();
      this._tempProfileData = { ...originalProfile };
    }
    
    // Aktualisiere alle Formular-Felder
    for (const [key, value] of formData.entries()) {
      if (key === 'enabled') {
        this._tempProfileData[key] = true;  // Checkbox checked
      } else if (form.elements[key].type === 'number') {
        this._tempProfileData[key] = value ? parseFloat(value) : 0;
      } else {
        this._tempProfileData[key] = value;
      }
    }
    
    // Checkbox-Felder die nicht in FormData sind (unchecked)
    const checkboxes = form.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(cb => {
      if (!formData.has(cb.name)) {
        this._tempProfileData[cb.name] = false;
      }
    });
    
    console.log('💾 Formular-Daten zwischengespeichert:', this._tempProfileData);
  }

  _closeDialog() {
    this._editingProfile = null;
    this._editingArea = null;
    this._editDialogTab = 'basic';
    this._tempProfileData = null;  // Lösche temporäre Daten
    this.render();
  }

  async _saveProfile() {
    const form = this.shadowRoot.querySelector('#profile-form');
    if (!form) return;

    const formData = new FormData(form);
    const profile = {};

    // Text inputs
    ['name', 'cover', 'area', 'window_sensor', 'door_sensor', 'lux_sensor', 'temp_sensor', 'intermediate_time'].forEach(field => {
      const value = formData.get(field);
      profile[field] = value === '' ? null : value;
    });

    // Number inputs
    ['day_pos', 'night_pos', 'vent_pos', 'door_safe', 'cooldown', 'lux_th', 'lux_hysteresis', 
     'temp_th', 'temp_hysteresis', 'az_min', 'az_max', 'shade_pos', 'window_open_delay', 
     'window_close_delay', 'heat_protection_temp', 'intermediate_pos', 'brightness_end_delay'].forEach(field => {
      const value = formData.get(field);
      profile[field] = value ? parseFloat(value) : 0;
    });

    // Checkboxes
    ['enabled', 'heat_protection', 'no_close_summer', 'keep_sunprotect'].forEach(field => {
      profile[field] = formData.get(field) === 'on';
    });

    // Validation
    if (!profile.name || !profile.cover) {
      alert('Bitte fülle mindestens Name und Cover Entity aus!');
      return;
    }

    // Save
    const index = this._editingProfile.index;
    if (index === -1) {
      this._profiles.push(profile);
    } else {
      // Preserve runtime data
      const oldProfile = this._profiles[index];
      this._profiles[index] = { ...profile, status: oldProfile.status, _entities: oldProfile._entities };
    }

    await this._saveConfig();
    this._closeDialog();
    this._showToast(index === -1 ? 'Profil erstellt' : 'Profil gespeichert');
  }

  async _saveArea() {
    const form = this.shadowRoot.querySelector('#area-form');
    if (!form) return;

    const formData = new FormData(form);
    const areaKey = this._editingArea;
    const area = {};

    ['name', 'mode', 'up_time_week', 'down_time_week', 'up_time_weekend', 
     'down_time_weekend', 'up_earliest', 'up_latest'].forEach(field => {
      area[field] = formData.get(field) || '';
    });

    area.stagger_delay = parseInt(formData.get('stagger_delay')) || 0;

    this._areas[areaKey] = area;
    await this._saveConfig();
    this._closeDialog();
    this._showToast('Bereich gespeichert');
  }

  async _saveConfig() {
    if (!this._configEntry) {
      this._showToast('Config Entry nicht gefunden', 'error');
      console.error('❌ _saveConfig: Config Entry nicht gefunden');
      return;
    }

    try {
      // Bereinige Profile (entferne Runtime-Daten)
      const cleanProfiles = this._profiles.map(p => {
        const clean = { ...p };
        delete clean.status;
        delete clean._entities;
        return clean;
      });

      console.log('💾 Speichere Config:', {
        profiles: cleanProfiles.length,
        areas: Object.keys(this._areas).length
      });

      // Nutze den update_config Service (triggert automatisch Integration-Reload)
      await this._hass.callService('shutterpilot', 'update_config', {
        profiles: cleanProfiles,
        areas: this._areas,
      });

      console.log('✅ Service-Call erfolgreich, Integration lädt neu...');

      this._showToast('Konfiguration gespeichert', 'success');

      // Warte auf Integration-Reload (ca. 2-3 Sekunden), dann Config neu laden
      setTimeout(async () => {
        console.log('🔄 Lade Config neu nach Integration-Reload...');
        await this._loadConfigEntry();
        this.render();
        console.log('✅ Config erfolgreich neu geladen');
      }, 2500);

    } catch (err) {
      console.error('Fehler beim Speichern:', err);
      this._showToast(`Fehler beim Speichern: ${err.message}`, 'error');
    }
  }

  async _toggleProfileEnabled(index) {
    const profile = this._profiles[index];
    if (!profile || !profile._entities?.switch) {
      this._showToast('Switch-Entity nicht gefunden', 'error');
      return;
    }

    const service = profile.enabled ? 'turn_off' : 'turn_on';
    
    try {
      await this._hass.callService('switch', service, {
        entity_id: profile._entities.switch
      });
      this._showToast(`Profil ${profile.enabled ? 'deaktiviert' : 'aktiviert'}`);
      
      setTimeout(() => this._refresh(), 500);
    } catch (err) {
      this._showToast(`Fehler: ${err.message}`, 'error');
    }
  }

  async _callService(service) {
    if (!this._hass) return;
    
    try {
      await this._hass.callService('shutterpilot', service, {});
      this._showToast(`Service "${service}" ausgeführt`);
    } catch (err) {
      this._showToast(`Fehler: ${err.message}`, 'error');
      console.error('Service call error:', err);
    }
  }

  async _toggleGlobalAuto(checked) {
    if (!this._hass) return;
    
    const service = checked ? 'turn_on' : 'turn_off';
    try {
      await this._hass.callService('switch', service, {
        entity_id: this._config.entity
      });
      this._showToast(`Globale Automatik ${checked ? 'aktiviert' : 'deaktiviert'}`);
      
      setTimeout(() => this.render(), 300);
    } catch (err) {
      this._showToast(`Fehler: ${err.message}`, 'error');
      console.error('Toggle global auto error:', err);
    }
  }

  // Helper Functions
  _getStatusClass(status) {
    const map = {
      'active': 'active',
      'inactive': 'inactive',
      'cooldown': 'cooldown',
      'idle': 'inactive',
    };
    return map[status?.toLowerCase()] || 'unknown';
  }

  _getStatusText(status) {
    const map = {
      'active': 'Aktiv',
      'inactive': 'Inaktiv',
      'cooldown': 'Cooldown',
      'idle': 'Bereit',
      'unknown': 'Unbekannt',
    };
    return map[status?.toLowerCase()] || status || 'Unbekannt';
  }

  _getModeText(mode) {
    const map = {
      'time_only': 'Nur Zeit',
      'sun': 'Sonnenstand',
      'golden_hour': 'Golden Hour',
      'brightness': 'Helligkeitssensor',
    };
    return map[mode] || mode || 'Unbekannt';
  }

  _formatDate(dateStr) {
    if (!dateStr) return '-';
    const parts = dateStr.split('-');
    if (parts.length !== 2) return dateStr;
    return `${parts[1]}.${parts[0]}.`;
  }

  _showToast(message, type = 'info') {
    const event = new CustomEvent('hass-notification', {
      bubbles: true,
      composed: true,
      detail: { message }
    });
    this.dispatchEvent(event);

    const prefix = type === 'error' ? '❌' : type === 'warning' ? '⚠️' : '✅';
    console.log(`${prefix} ${message}`);
  }

  _getStyles() {
    return `
      :host {
        display: block;
      }

      * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
      }

      .card-container {
        background: var(--card-background-color, #1c1c1e);
        border-radius: var(--ha-card-border-radius, 12px);
        box-shadow: var(--ha-card-box-shadow, 0 2px 8px rgba(0,0,0,0.3));
        overflow: hidden;
        color: var(--primary-text-color, #e1e1e1);
      }

      /* Header - Dark Mode optimiert */
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 24px;
        background: linear-gradient(135deg, #1a73e8, #0d47a1);
        color: white;
      }

      .header-left {
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .header-left ha-icon {
        --mdc-icon-size: 32px;
      }

      .card-header h1 {
        font-size: 24px;
        font-weight: 600;
      }

      .subtitle {
        font-size: 12px;
        opacity: 0.9;
      }

      .header-right {
        display: flex;
        gap: 8px;
      }

      .icon-button {
        background: rgba(255,255,255,0.15);
        border: none;
        border-radius: 8px;
        width: 40px;
        height: 40px;
        cursor: pointer;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s;
      }

      .icon-button:hover {
        background: rgba(255,255,255,0.25);
        transform: scale(1.05);
      }

      /* Tabs - Dark Mode */
      .tabs {
        display: flex;
        border-bottom: 1px solid var(--divider-color, #333);
        background: var(--primary-background-color, #2c2c2e);
      }

      .tab {
        flex: 1;
        padding: 16px 24px;
        border: none;
        background: transparent;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        color: var(--secondary-text-color, #999);
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        transition: all 0.2s;
        border-bottom: 3px solid transparent;
      }

      .tab:hover {
        background: rgba(255,255,255,0.05);
        color: var(--primary-text-color, #e1e1e1);
      }

      .tab.active {
        color: #1a73e8;
        border-bottom-color: #1a73e8;
        background: var(--card-background-color, #1c1c1e);
      }

      /* Content - Dark Mode */
      .card-content {
        padding: 24px;
        min-height: 300px;
        background: var(--card-background-color, #1c1c1e);
      }

      /* Empty State */
      .empty-state {
        text-align: center;
        padding: 60px 20px;
        color: var(--secondary-text-color, #999);
      }

      .empty-state ha-icon {
        --mdc-icon-size: 64px;
        color: var(--disabled-text-color, #666);
        margin-bottom: 20px;
      }

      .empty-state h3 {
        font-size: 20px;
        margin-bottom: 8px;
        color: var(--primary-text-color, #e1e1e1);
      }

      .empty-state p {
        margin-bottom: 24px;
      }

      /* Toolbar */
      .toolbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        flex-wrap: wrap;
        gap: 12px;
      }

      .toolbar-actions {
        display: flex;
        gap: 8px;
      }

      /* Buttons - Dark Mode */
      .btn {
        padding: 10px 20px;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        transition: all 0.2s;
        font-family: inherit;
      }

      .btn-primary {
        background: #1a73e8;
        color: white;
      }

      .btn-primary:hover {
        background: #1557b0;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(26, 115, 232, 0.4);
      }

      .btn-secondary {
        background: var(--secondary-background-color, #2c2c2e);
        color: var(--primary-text-color, #e1e1e1);
        border: 1px solid var(--divider-color, #444);
      }

      .btn-secondary:hover {
        background: var(--divider-color, #3a3a3c);
      }

      .btn-block {
        width: 100%;
        justify-content: center;
      }

      .btn-icon {
        background: transparent;
        border: none;
        padding: 6px;
        cursor: pointer;
        border-radius: 6px;
        color: var(--secondary-text-color, #999);
        transition: all 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .btn-icon:hover {
        background: rgba(255,255,255,0.1);
        color: var(--primary-text-color, #e1e1e1);
      }

      .btn-icon-dialog {
        background: transparent;
        border: none;
        padding: 8px;
        cursor: pointer;
        border-radius: 8px;
        color: var(--secondary-text-color, #999);
        transition: all 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .btn-icon-dialog:hover {
        background: rgba(255,255,255,0.1);
        color: var(--primary-text-color, #e1e1e1);
      }

      /* Table - Dark Mode optimiert */
      .profile-table {
        background: var(--card-background-color, #1c1c1e);
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--divider-color, #333);
      }

      .table-header {
        display: flex;
        background: var(--secondary-background-color, #2c2c2e);
        font-weight: 600;
        font-size: 12px;
        text-transform: uppercase;
        color: var(--secondary-text-color, #999);
        padding: 12px 16px;
        border-bottom: 2px solid var(--divider-color, #444);
      }

      .table-row {
        display: flex;
        align-items: center;
        padding: 16px;
        border-bottom: 1px solid var(--divider-color, #2a2a2c);
        transition: all 0.2s;
        background: var(--card-background-color, #1c1c1e);
      }

      .table-row:last-child {
        border-bottom: none;
      }

      .table-row:hover {
        background: rgba(255,255,255,0.05);
      }

      .table-row.disabled {
        opacity: 0.5;
      }

      .th, .td {
        padding: 0 8px;
      }

      .th-status, .td-status { width: 100px; }
      .th-name, .td-name { flex: 1; min-width: 150px; }
      .th-cover, .td-cover { flex: 1; min-width: 200px; }
      .th-area, .td-area { width: 140px; }
      .th-sensors, .td-sensors { width: 120px; }
      .th-actions, .td-actions { width: 180px; }

      .td-name strong {
        font-weight: 600;
        color: var(--primary-text-color, #e1e1e1);
      }

      .disabled-label {
        font-size: 11px;
        color: var(--secondary-text-color, #999);
        font-weight: normal;
        margin-left: 8px;
      }

      .td-cover code {
        background: var(--secondary-background-color, #2c2c2e);
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-family: 'Courier New', monospace;
        color: #4fc3f7;
      }

      /* Status Badge - High Contrast */
      .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
      }

      .status-active {
        background: #1b5e20;
        color: #76ff03;
      }

      .status-inactive {
        background: #424242;
        color: #bdbdbd;
      }

      .status-cooldown {
        background: #f57f17;
        color: #fff59d;
      }

      .status-unknown {
        background: #b71c1c;
        color: #ff8a80;
      }

      /* Area Badge */
      .area-badge {
        display: inline-block;
        padding: 4px 10px;
        background: #1a73e8;
        color: white;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 500;
      }

      /* Sensor Icons */
      .sensor-icons {
        display: flex;
        gap: 6px;
      }

      .sensor-icons ha-icon {
        --mdc-icon-size: 18px;
        color: var(--secondary-text-color, #999);
      }

      .no-sensors {
        font-size: 12px;
        color: var(--disabled-text-color, #666);
      }

      /* Action Buttons */
      .action-btn {
        background: transparent;
        border: none;
        padding: 6px;
        cursor: pointer;
        border-radius: 6px;
        color: var(--secondary-text-color, #999);
        transition: all 0.2s;
        display: inline-flex;
        align-items: center;
        justify-content: center;
      }

      .action-btn:hover {
        background: rgba(255,255,255,0.1);
        color: var(--primary-text-color, #e1e1e1);
        transform: scale(1.1);
      }

      .action-delete:hover {
        background: #b71c1c;
        color: #ff8a80;
      }

      /* Areas Grid */
      .areas-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 20px;
      }

      .area-card {
        background: var(--secondary-background-color, #2c2c2e);
        border: 1px solid var(--divider-color, #444);
        border-radius: 12px;
        padding: 20px;
        transition: all 0.2s;
      }

      .area-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        transform: translateY(-2px);
        border-color: #1a73e8;
      }

      .area-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 2px solid #1a73e8;
      }

      .area-header h3 {
        font-size: 18px;
        font-weight: 600;
        color: var(--primary-text-color, #e1e1e1);
      }

      .area-info .info-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid var(--divider-color, #333);
      }

      .area-info .info-row:last-child {
        border-bottom: none;
      }

      .area-info .label {
        font-size: 13px;
        color: var(--secondary-text-color, #999);
      }

      .area-info .value {
        font-size: 13px;
        font-weight: 500;
        color: var(--primary-text-color, #e1e1e1);
      }

      /* Global Settings */
      .global-settings {
        max-width: 900px;
        margin: 0 auto;
      }

      .setting-card {
        background: var(--secondary-background-color, #2c2c2e);
        border: 1px solid var(--divider-color, #444);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
      }

      .setting-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
      }

      .setting-header h3 {
        font-size: 18px;
        font-weight: 600;
        color: var(--primary-text-color, #e1e1e1);
        margin: 0;
      }

      .setting-description {
        font-size: 14px;
        color: var(--secondary-text-color, #999);
        margin: 0;
      }

      .setting-card h3 {
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 16px;
        color: var(--primary-text-color, #e1e1e1);
      }

      .info-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
      }

      .info-item {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }

      .info-item .label {
        font-size: 12px;
        color: var(--secondary-text-color, #999);
      }

      .info-item .value {
        font-size: 16px;
        font-weight: 600;
        color: var(--primary-text-color, #e1e1e1);
      }

      .badge {
        background: #1a73e8;
        color: white;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 14px;
        display: inline-block;
      }

      .service-buttons {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      /* Toggle Switch - Dark Mode */
      .switch {
        position: relative;
        display: inline-block;
        width: 50px;
        height: 28px;
      }

      .switch input {
        opacity: 0;
        width: 0;
        height: 0;
      }

      .slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #666;
        transition: .3s;
        border-radius: 28px;
      }

      .slider:before {
        position: absolute;
        content: "";
        height: 20px;
        width: 20px;
        left: 4px;
        bottom: 4px;
        background-color: white;
        transition: .3s;
        border-radius: 50%;
      }

      input:checked + .slider {
        background-color: #1a73e8;
      }

      input:checked + .slider:before {
        transform: translateX(22px);
      }

      /* Dialog - Dark Mode */
      .dialog-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        padding: 20px;
      }

      .dialog {
        background: var(--card-background-color, #1c1c1e);
        border-radius: 16px;
        max-width: 800px;
        width: 100%;
        max-height: 90vh;
        display: flex;
        flex-direction: column;
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        border: 1px solid var(--divider-color, #444);
      }

      .dialog-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 24px;
        border-bottom: 1px solid var(--divider-color, #333);
      }

      .dialog-header h2 {
        margin: 0;
        font-size: 20px;
        font-weight: 600;
        color: var(--primary-text-color, #e1e1e1);
      }

      .dialog-tabs {
        display: flex;
        border-bottom: 1px solid var(--divider-color, #333);
        padding: 0 24px;
        background: var(--secondary-background-color, #2c2c2e);
      }

      .dialog-tab {
        padding: 12px 20px;
        border: none;
        background: transparent;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        color: var(--secondary-text-color, #999);
        border-bottom: 2px solid transparent;
        transition: all 0.2s;
      }

      .dialog-tab:hover {
        color: var(--primary-text-color, #e1e1e1);
      }

      .dialog-tab.active {
        color: #1a73e8;
        border-bottom-color: #1a73e8;
      }

      .dialog-content {
        flex: 1;
        overflow-y: auto;
        padding: 24px;
      }

      .dialog-footer {
        display: flex;
        justify-content: flex-end;
        gap: 12px;
        padding: 20px 24px;
        border-top: 1px solid var(--divider-color, #333);
      }

      /* Form - Dark Mode optimiert */
      .form-group {
        margin-bottom: 20px;
      }

      .form-group label {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
        font-size: 14px;
        font-weight: 500;
        color: var(--primary-text-color, #e1e1e1);
      }

      .form-group label ha-icon {
        --mdc-icon-size: 20px;
        color: var(--secondary-text-color, #999);
      }

      .form-hint {
        display: block;
        margin-top: 6px;
        font-size: 12px;
        color: var(--secondary-text-color, #999);
      }

      .highlight-sensor {
        background: rgba(26, 115, 232, 0.1);
        padding: 16px;
        border-radius: 8px;
        border: 2px solid rgba(26, 115, 232, 0.3);
      }

      .highlight-sensor label {
        color: #4fc3f7;
        font-weight: 600;
      }

      .highlight-sensor label ha-icon {
        color: #ffeb3b;
      }

      .form-input {
        width: 100%;
        padding: 10px 12px;
        border: 1px solid var(--divider-color, #444);
        border-radius: 8px;
        font-size: 14px;
        font-family: inherit;
        background: var(--secondary-background-color, #2c2c2e);
        color: var(--primary-text-color, #e1e1e1);
        transition: all 0.2s;
      }

      .form-input:focus {
        outline: none;
        border-color: #1a73e8;
        box-shadow: 0 0 0 3px rgba(26, 115, 232, 0.2);
      }

      .form-input option {
        background: var(--card-background-color, #1c1c1e);
        color: var(--primary-text-color, #e1e1e1);
      }

      .form-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
      }

      .form-section-title {
        font-size: 16px;
        font-weight: 600;
        margin: 24px 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid var(--divider-color, #444);
        color: var(--primary-text-color, #e1e1e1);
      }

      .checkbox-label {
        display: flex;
        align-items: center;
        gap: 12px;
        cursor: pointer;
        user-select: none;
      }

      .checkbox-label input[type="checkbox"] {
        width: 20px;
        height: 20px;
        cursor: pointer;
      }

      .checkbox-label span {
        font-size: 14px;
        color: var(--primary-text-color, #e1e1e1);
      }

      /* Responsive */
      @media (max-width: 768px) {
        .table-header {
          display: none;
        }

        .table-row {
          flex-direction: column;
          align-items: stretch;
          gap: 12px;
        }

        .th, .td {
          width: 100% !important;
          flex: none !important;
        }

        .toolbar {
          flex-direction: column;
          align-items: stretch;
        }

        .toolbar-actions {
          justify-content: space-between;
        }

        .areas-grid {
          grid-template-columns: 1fr;
        }

        .info-grid {
          grid-template-columns: 1fr;
        }

        .form-row {
          grid-template-columns: 1fr;
        }
      }
    `;
  }

  getCardSize() {
    return 8;
  }
}

customElements.define('shutterpilot-card', ShutterPilotCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'shutterpilot-card',
  name: 'ShutterPilot Management Card',
  description: 'Professional management card for ShutterPilot - Dark Mode + Full Configuration',
  preview: true,
  documentationURL: 'https://github.com/fschube/shutterpilot'
});

console.info(
  '%c  SHUTTERPILOT-CARD  \n%c  Version 2.2.1 - Save to Backend Fixed ',
  'color: white; background: #1a73e8; font-weight: 700;',
  'color: #1a73e8; font-weight: 300;'
);
