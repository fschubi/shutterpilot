/**
 * ShutterPilot Management Card
 * Professional Enterprise-Level UI for ShutterPilot
 * Version: 1.0.0 - Production Ready
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
    this._editDialogTab = 'basic';
    this._activeTab = 'profiles';
    this._selectedProfiles = new Set();
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
    
    // Initial load oder wenn Config Entry sich ändert
    if (!oldHass || this._needsUpdate(oldHass, hass)) {
      this._loadConfigEntry();
    }
    
    this.render();
  }

  _needsUpdate(oldHass, newHass) {
    // Prüfe ob sich relevante States geändert haben
    const oldGlobal = oldHass?.states[this._config.entity];
    const newGlobal = newHass?.states[this._config.entity];
    
    if (oldGlobal?.state !== newGlobal?.state) return true;
    
    // Prüfe Profil-Switches
    const oldSwitches = Object.keys(oldHass?.states || {}).filter(e => e.startsWith('switch.shutterpilot_'));
    const newSwitches = Object.keys(newHass?.states || {}).filter(e => e.startsWith('switch.shutterpilot_'));
    
    if (oldSwitches.length !== newSwitches.length) return true;
    
    return false;
  }

  async _loadConfigEntry() {
    if (!this._hass) return;

    try {
      // Hole die Config Entry via WebSocket
      const entries = await this._hass.callWS({
        type: 'config_entries/get',
      });

      // Finde ShutterPilot Entry
      const spEntry = entries.find(e => e.domain === 'shutterpilot');
      
      if (!spEntry) {
        console.warn('ShutterPilot Integration nicht gefunden');
        return;
      }

      this._configEntry = spEntry;
      
      // Extrahiere Profile und Areas aus den Options
      const options = spEntry.options || {};
      this._profiles = options.profiles || [];
      this._areas = options.areas || this._getDefaultAreas();
      this._globalSettings = {
        default_vpos: options.default_vpos || 30,
        default_cooldown: options.default_cooldown || 120,
        summer_start: options.summer_start || '05-01',
        summer_end: options.summer_end || '09-30',
        sun_elevation_end: options.sun_elevation_end || 3.0,
        sun_offset_up: options.sun_offset_up || 0,
        sun_offset_down: options.sun_offset_down || 0,
      };

      // Ergänze Profile mit Live-Status aus Sensoren
      this._enrichProfilesWithStatus();

    } catch (err) {
      console.error('Fehler beim Laden der Config Entry:', err);
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
      
      // Hole Status-Sensor
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
        ${this._editingProfile !== null ? this._renderEditDialog() : ''}
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
          <button class="icon-button" onclick="window.spCard._refresh()">
            <ha-icon icon="mdi:refresh"></ha-icon>
          </button>
          <button class="icon-button" onclick="window.spCard._openIntegrationConfig()">
            <ha-icon icon="mdi:cog"></ha-icon>
          </button>
        </div>
      </div>
    `;
  }

  _renderTabs() {
    return `
      <div class="tabs">
        <button class="tab ${this._activeTab === 'profiles' ? 'active' : ''}" 
                onclick="window.spCard._setTab('profiles')">
          <ha-icon icon="mdi:view-list"></ha-icon>
          Profile
        </button>
        <button class="tab ${this._activeTab === 'areas' ? 'active' : ''}" 
                onclick="window.spCard._setTab('areas')">
          <ha-icon icon="mdi:home-group"></ha-icon>
          Bereiche
        </button>
        <button class="tab ${this._activeTab === 'global' ? 'active' : ''}" 
                onclick="window.spCard._setTab('global')">
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
          <p>Erstelle dein erstes Profil über die Integration-Einstellungen</p>
          <button class="btn btn-primary" onclick="window.spCard._openIntegrationConfig()">
            <ha-icon icon="mdi:cog"></ha-icon>
            Zu den Einstellungen
          </button>
        </div>
      `;
    }

    return `
      <div class="toolbar">
        <button class="btn btn-primary" onclick="window.spCard._openIntegrationConfig()">
          <ha-icon icon="mdi:plus"></ha-icon>
          Neues Profil
        </button>
        <div class="toolbar-actions">
          <button class="btn btn-secondary" onclick="window.spCard._callService('all_up')">
            <ha-icon icon="mdi:arrow-up"></ha-icon>
            Alle hoch
          </button>
          <button class="btn btn-secondary" onclick="window.spCard._callService('all_down')">
            <ha-icon icon="mdi:arrow-down"></ha-icon>
            Alle runter
          </button>
          <button class="btn btn-secondary" onclick="window.spCard._callService('stop')">
            <ha-icon icon="mdi:stop"></ha-icon>
            Stopp
          </button>
        </div>
      </div>

      <div class="profile-table">
        <div class="table-header">
          <div class="th th-checkbox">
            <input type="checkbox" onchange="window.spCard._toggleAllProfiles(this.checked)">
          </div>
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
        <div class="td td-checkbox">
          <input type="checkbox" 
                 ${this._selectedProfiles.has(index) ? 'checked' : ''}
                 onchange="window.spCard._toggleProfile(${index}, this.checked)">
        </div>
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
          <button class="action-btn" onclick="window.spCard._showProfileInfo(${index})" title="Info">
            <ha-icon icon="mdi:information"></ha-icon>
          </button>
          <button class="action-btn" onclick="window.spCard._toggleProfileEnabled(${index})" 
                  title="${profile.enabled ? 'Deaktivieren' : 'Aktivieren'}">
            <ha-icon icon="${profile.enabled ? 'mdi:pause' : 'mdi:play'}"></ha-icon>
          </button>
          <button class="action-btn" onclick="window.spCard._openIntegrationConfig()" title="Bearbeiten">
            <ha-icon icon="mdi:pencil"></ha-icon>
          </button>
          <button class="action-btn action-delete" onclick="window.spCard._deleteProfile(${index})" title="Löschen">
            <ha-icon icon="mdi:delete"></ha-icon>
          </button>
        </div>
      </div>
    `;
  }

  _renderAreasTab() {
    const areas = Object.entries(this._areas);
    
    if (areas.length === 0) {
      return `
        <div class="empty-state">
          <ha-icon icon="mdi:home-group"></ha-icon>
          <h3>Keine Bereiche konfiguriert</h3>
          <p>Konfiguriere Bereiche über die Integration-Einstellungen</p>
        </div>
      `;
    }

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
          <button class="btn-icon" onclick="window.spCard._openIntegrationConfig()" title="Bearbeiten">
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
            <span class="label">Früheste Hochfahrzeit:</span>
            <span class="value">${area.up_earliest || '-'}</span>
          </div>
          <div class="info-row">
            <span class="label">Späteste Hochfahrzeit:</span>
            <span class="value">${area.up_latest || '-'}</span>
          </div>
          <div class="info-row">
            <span class="label">Verzögerung:</span>
            <span class="value">${area.stagger_delay || 0}s</span>
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
              <input type="checkbox" ${isOn ? 'checked' : ''} 
                     onchange="window.spCard._toggleGlobalAuto(this.checked)">
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
            <button class="btn btn-block btn-secondary" onclick="window.spCard._callService('recalculate_now')">
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
          <h3>Sonnen-Einstellungen</h3>
          <div class="info-grid">
            <div class="info-item">
              <span class="label">Sonnenhöhe Ende:</span>
              <span class="value">${this._globalSettings.sun_elevation_end}°</span>
            </div>
            <div class="info-item">
              <span class="label">Offset Hochfahren:</span>
              <span class="value">${this._globalSettings.sun_offset_up} Min</span>
            </div>
            <div class="info-item">
              <span class="label">Offset Runterfahren:</span>
              <span class="value">${this._globalSettings.sun_offset_down} Min</span>
            </div>
          </div>
        </div>

        <div class="setting-card">
          <h3>Standard-Werte</h3>
          <div class="info-grid">
            <div class="info-item">
              <span class="label">Lüftungsposition:</span>
              <span class="value">${this._globalSettings.default_vpos}%</span>
            </div>
            <div class="info-item">
              <span class="label">Cooldown:</span>
              <span class="value">${this._globalSettings.default_cooldown}s</span>
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

        <div class="setting-card">
          <h3>Einstellungen</h3>
          <button class="btn btn-block btn-primary" onclick="window.spCard._openIntegrationConfig()">
            <ha-icon icon="mdi:cog"></ha-icon>
            Integration konfigurieren
          </button>
        </div>
      </div>
    `;
  }

  _renderEditDialog() {
    // Für zukünftige Implementierung - derzeit öffnen wir immer die Integration-Config
    return '';
  }

  // Event Handlers
  _attachEventListeners() {
    window.spCard = this;
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

  _openIntegrationConfig() {
    if (!this._configEntry) {
      this._showToast('Config Entry nicht gefunden', 'error');
      return;
    }

    const event = new Event('config-entry-open', {
      bubbles: true,
      composed: true,
    });
    event.detail = { entry_id: this._configEntry.entry_id };
    this.dispatchEvent(event);

    // Alternative: Öffne Integrations-Seite
    window.location.href = `/config/integrations/integration/shutterpilot`;
  }

  _toggleAllProfiles(checked) {
    if (checked) {
      this._profiles.forEach((_, idx) => this._selectedProfiles.add(idx));
    } else {
      this._selectedProfiles.clear();
    }
    this.render();
  }

  _toggleProfile(index, checked) {
    if (checked) {
      this._selectedProfiles.add(index);
    } else {
      this._selectedProfiles.delete(index);
    }
    this.render();
  }

  async _toggleProfileEnabled(index) {
    const profile = this._profiles[index];
    if (!profile || !profile._entities?.switch) return;

    const service = profile.enabled ? 'turn_off' : 'turn_on';
    
    try {
      await this._hass.callService('switch', service, {
        entity_id: profile._entities.switch
      });
      this._showToast(`Profil ${profile.enabled ? 'deaktiviert' : 'aktiviert'}`);
      
      // Warte kurz und aktualisiere
      setTimeout(() => this._refresh(), 500);
    } catch (err) {
      this._showToast(`Fehler: ${err.message}`, 'error');
    }
  }

  _showProfileInfo(index) {
    const profile = this._profiles[index];
    if (!profile) return;

    const info = `
      <strong>${profile.name}</strong><br><br>
      <strong>Cover:</strong> ${profile.cover}<br>
      <strong>Bereich:</strong> ${profile.area ? this._areas[profile.area]?.name : 'Keiner'}<br>
      <strong>Status:</strong> ${this._getStatusText(profile.status)}<br>
      <strong>Enabled:</strong> ${profile.enabled ? 'Ja' : 'Nein'}<br><br>
      
      <strong>Sensoren:</strong><br>
      ${profile.window_sensor ? `Fenster: ${profile.window_sensor}<br>` : ''}
      ${profile.door_sensor ? `Tür: ${profile.door_sensor}<br>` : ''}
      ${profile.lux_sensor ? `Helligkeit: ${profile.lux_sensor}<br>` : ''}
      ${profile.temp_sensor ? `Temperatur: ${profile.temp_sensor}<br>` : ''}
      ${!profile.window_sensor && !profile.door_sensor && !profile.lux_sensor && !profile.temp_sensor ? 'Keine Sensoren konfiguriert' : ''}
    `;

    this._showDialog('Profil-Information', info);
  }

  async _deleteProfile(index) {
    const profile = this._profiles[index];
    if (!profile) return;

    if (!confirm(`Profil "${profile.name}" wirklich löschen?`)) return;

    // Öffne Integration-Config zum Löschen
    this._showToast('Bitte lösche das Profil über die Integration-Einstellungen', 'warning');
    this._openIntegrationConfig();
  }

  async _callService(service) {
    if (!this._hass) return;
    
    try {
      await this._hass.callService('shutterpilot', service, {});
      this._showToast(`Service "${service}" ausgeführt`);
    } catch (err) {
      this._showToast(`Fehler: ${err.message}`, 'error');
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
      this.render();
    } catch (err) {
      this._showToast(`Fehler: ${err.message}`, 'error');
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
    };
    return map[mode] || mode || 'Unbekannt';
  }

  _formatDate(dateStr) {
    if (!dateStr) return '-';
    // Format: MM-DD -> DD.MM.
    const parts = dateStr.split('-');
    if (parts.length !== 2) return dateStr;
    return `${parts[1]}.${parts[0]}.`;
  }

  _showToast(message, type = 'info') {
    const event = new Event('hass-notification', {
      bubbles: true,
      composed: true,
    });
    event.detail = { message };
    this.dispatchEvent(event);

    // Fallback: Console
    const prefix = type === 'error' ? '❌' : type === 'warning' ? '⚠️' : '✅';
    console.log(`${prefix} ${message}`);
  }

  _showDialog(title, content) {
    const event = new Event('hass-more-info', {
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);

    // Fallback: alert
    alert(`${title}\n\n${content.replace(/<br>/g, '\n').replace(/<[^>]*>/g, '')}`);
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
        background: var(--ha-card-background, var(--card-background-color, white));
        border-radius: var(--ha-card-border-radius, 12px);
        box-shadow: var(--ha-card-box-shadow, 0 2px 8px rgba(0,0,0,0.1));
        overflow: hidden;
      }

      /* Header */
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 24px;
        background: linear-gradient(135deg, var(--primary-color, #3b82f6), var(--primary-color-dark, #2563eb));
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
        background: rgba(255,255,255,0.2);
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
        background: rgba(255,255,255,0.3);
        transform: scale(1.05);
      }

      /* Tabs */
      .tabs {
        display: flex;
        border-bottom: 1px solid var(--divider-color, #e5e7eb);
        background: var(--primary-background-color, #fafafa);
      }

      .tab {
        flex: 1;
        padding: 16px 24px;
        border: none;
        background: transparent;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        color: var(--secondary-text-color, #6b7280);
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        transition: all 0.2s;
        border-bottom: 3px solid transparent;
      }

      .tab:hover {
        background: rgba(0,0,0,0.05);
      }

      .tab.active {
        color: var(--primary-color, #3b82f6);
        border-bottom-color: var(--primary-color, #3b82f6);
        background: white;
      }

      /* Content */
      .card-content {
        padding: 24px;
        min-height: 300px;
      }

      /* Empty State */
      .empty-state {
        text-align: center;
        padding: 60px 20px;
        color: var(--secondary-text-color, #6b7280);
      }

      .empty-state ha-icon {
        --mdc-icon-size: 64px;
        color: var(--disabled-text-color, #9ca3af);
        margin-bottom: 20px;
      }

      .empty-state h3 {
        font-size: 20px;
        margin-bottom: 8px;
        color: var(--primary-text-color);
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

      /* Buttons */
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
        background: var(--primary-color, #3b82f6);
        color: white;
      }

      .btn-primary:hover {
        background: var(--primary-color-dark, #2563eb);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
      }

      .btn-secondary {
        background: var(--secondary-background-color, #f3f4f6);
        color: var(--primary-text-color, #111827);
      }

      .btn-secondary:hover {
        background: var(--divider-color, #e5e7eb);
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
        color: var(--secondary-text-color, #6b7280);
        transition: all 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .btn-icon:hover {
        background: var(--secondary-background-color, #f3f4f6);
        color: var(--primary-text-color);
      }

      /* Table */
      .profile-table {
        background: white;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--divider-color, #e5e7eb);
      }

      .table-header {
        display: flex;
        background: var(--secondary-background-color, #f9fafb);
        font-weight: 600;
        font-size: 12px;
        text-transform: uppercase;
        color: var(--secondary-text-color, #6b7280);
        padding: 12px 16px;
        border-bottom: 2px solid var(--divider-color, #e5e7eb);
      }

      .table-row {
        display: flex;
        align-items: center;
        padding: 16px;
        border-bottom: 1px solid var(--divider-color, #e5e7eb);
        transition: all 0.2s;
      }

      .table-row:last-child {
        border-bottom: none;
      }

      .table-row:hover {
        background: var(--primary-background-color, #f9fafb);
      }

      .table-row.disabled {
        opacity: 0.6;
      }

      .th, .td {
        padding: 0 8px;
      }

      .th-checkbox, .td-checkbox { width: 50px; }
      .th-status, .td-status { width: 100px; }
      .th-name, .td-name { flex: 1; min-width: 150px; }
      .th-cover, .td-cover { flex: 1; min-width: 200px; }
      .th-area, .td-area { width: 140px; }
      .th-sensors, .td-sensors { width: 120px; }
      .th-actions, .td-actions { width: 180px; }

      .td-name strong {
        font-weight: 600;
        color: var(--primary-text-color);
      }

      .disabled-label {
        font-size: 11px;
        color: var(--secondary-text-color);
        font-weight: normal;
        margin-left: 8px;
      }

      .td-cover code {
        background: var(--secondary-background-color, #f3f4f6);
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-family: 'Courier New', monospace;
      }

      /* Status Badge */
      .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
      }

      .status-active {
        background: #d1fae5;
        color: #065f46;
      }

      .status-inactive {
        background: #f3f4f6;
        color: #6b7280;
      }

      .status-cooldown {
        background: #fef3c7;
        color: #92400e;
      }

      .status-unknown {
        background: #fee2e2;
        color: #991b1b;
      }

      /* Area Badge */
      .area-badge {
        display: inline-block;
        padding: 4px 10px;
        background: var(--primary-color, #3b82f6);
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
        color: var(--secondary-text-color, #6b7280);
      }

      .no-sensors {
        font-size: 12px;
        color: var(--disabled-text-color, #9ca3af);
      }

      /* Action Buttons */
      .action-btn {
        background: transparent;
        border: none;
        padding: 6px;
        cursor: pointer;
        border-radius: 6px;
        color: var(--secondary-text-color, #6b7280);
        transition: all 0.2s;
        display: inline-flex;
        align-items: center;
        justify-content: center;
      }

      .action-btn:hover {
        background: var(--secondary-background-color, #f3f4f6);
        color: var(--primary-text-color);
      }

      .action-delete:hover {
        background: #fee2e2;
        color: #dc2626;
      }

      /* Areas Grid */
      .areas-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 20px;
      }

      .area-card {
        background: white;
        border: 1px solid var(--divider-color, #e5e7eb);
        border-radius: 12px;
        padding: 20px;
        transition: all 0.2s;
      }

      .area-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-2px);
      }

      .area-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 2px solid var(--primary-color, #3b82f6);
      }

      .area-header h3 {
        font-size: 18px;
        font-weight: 600;
        color: var(--primary-text-color);
      }

      .area-info .info-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid var(--divider-color, #e5e7eb);
      }

      .area-info .info-row:last-child {
        border-bottom: none;
      }

      .area-info .label {
        font-size: 13px;
        color: var(--secondary-text-color, #6b7280);
      }

      .area-info .value {
        font-size: 13px;
        font-weight: 500;
        color: var(--primary-text-color);
      }

      /* Global Settings */
      .global-settings {
        max-width: 900px;
        margin: 0 auto;
      }

      .setting-card {
        background: white;
        border: 1px solid var(--divider-color, #e5e7eb);
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
        color: var(--primary-text-color);
        margin: 0;
      }

      .setting-description {
        font-size: 14px;
        color: var(--secondary-text-color, #6b7280);
        margin: 0;
      }

      .setting-card h3 {
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 16px;
        color: var(--primary-text-color);
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
        color: var(--secondary-text-color, #6b7280);
      }

      .info-item .value {
        font-size: 16px;
        font-weight: 600;
        color: var(--primary-text-color);
      }

      .badge {
        background: var(--primary-color, #3b82f6);
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

      /* Toggle Switch */
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
        background-color: #ccc;
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
        background-color: var(--primary-color, #3b82f6);
      }

      input:checked + .slider:before {
        transform: translateX(22px);
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
      }
    `;
  }

  getCardSize() {
    return 8;
  }
}

// Registriere Custom Element
customElements.define('shutterpilot-card', ShutterPilotCard);

// Registriere in Lovelace
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'shutterpilot-card',
  name: 'ShutterPilot Management Card',
  description: 'Professional management card for ShutterPilot integration',
  preview: true,
  documentationURL: 'https://github.com/fschube/shutterpilot'
});

console.info(
  '%c  SHUTTERPILOT-CARD  \n%c  Version 1.0.0 - Production Ready ',
  'color: white; background: #3b82f6; font-weight: 700;',
  'color: #3b82f6; font-weight: 300;'
);
