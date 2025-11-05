/**
 * ShutterPilot Management Card
 * Professional Enterprise-Level UI for ShutterPilot
 * Version: 1.0.0
 */

class ShutterPilotCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._hass = null;
    this._config = null;
    this._profiles = [];
    this._areas = {};
    this._editingProfile = null;
    this._activeTab = 'profiles';
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('Please define an entity (switch.shutterpilot_global_automation)');
    }
    this._config = config;
  }

  set hass(hass) {
    this._hass = hass;
    this._updateData();
    this.render();
  }

  _updateData() {
    if (!this._hass) return;
    
    // Hole Config Entry Data
    const entries = Object.values(this._hass.states).filter(
      entity => entity.entity_id.startsWith('switch.shutterpilot_')
    );
    
    // TODO: Hole Profile und Areas aus der Integration
    // Für jetzt Mock-Daten
    this._profiles = [
      {
        name: 'Wohnzimmer',
        cover: 'cover.wohnzimmer_rollade',
        area: 'living',
        enabled: true,
        status: 'active'
      },
      {
        name: 'Schlafzimmer',
        cover: 'cover.schlafzimmer_rollade',
        area: 'sleeping',
        enabled: true,
        status: 'cooldown'
      }
    ];
    
    this._areas = {
      living: { name: 'Wohnbereich', mode: 'sun' },
      sleeping: { name: 'Schlafbereich', mode: 'sun' },
      children: { name: 'Kinderbereich', mode: 'time_only' }
    };
  }

  render() {
    if (!this._hass || !this._config) return;

    this.shadowRoot.innerHTML = `
      <style>
        ${this._getStyles()}
      </style>
      <div class="card-container">
        <div class="card-header">
          <div class="header-left">
            <ha-icon icon="mdi:window-shutter"></ha-icon>
            <h1>ShutterPilot</h1>
            <span class="subtitle">Enterprise Rollladensteuerung</span>
          </div>
          <div class="header-right">
            <button class="icon-button" @click="${() => this._refresh()}">
              <ha-icon icon="mdi:refresh"></ha-icon>
            </button>
            <button class="icon-button" @click="${() => this._openSettings()}">
              <ha-icon icon="mdi:cog"></ha-icon>
            </button>
          </div>
        </div>

        <div class="tabs">
          <button class="tab ${this._activeTab === 'profiles' ? 'active' : ''}" 
                  @click="${() => this._setTab('profiles')}">
            <ha-icon icon="mdi:view-list"></ha-icon>
            Profile
          </button>
          <button class="tab ${this._activeTab === 'areas' ? 'active' : ''}" 
                  @click="${() => this._setTab('areas')}">
            <ha-icon icon="mdi:home-group"></ha-icon>
            Bereiche
          </button>
          <button class="tab ${this._activeTab === 'global' ? 'active' : ''}" 
                  @click="${() => this._setTab('global')}">
            <ha-icon icon="mdi:cog-outline"></ha-icon>
            Global
          </button>
        </div>

        <div class="card-content">
          ${this._activeTab === 'profiles' ? this._renderProfilesTab() : ''}
          ${this._activeTab === 'areas' ? this._renderAreasTab() : ''}
          ${this._activeTab === 'global' ? this._renderGlobalTab() : ''}
        </div>

        ${this._editingProfile ? this._renderEditDialog() : ''}
      </div>
    `;

    this._attachEventListeners();
  }

  _renderProfilesTab() {
    return `
      <div class="toolbar">
        <button class="btn btn-primary" onclick="window.shutterpilotCard._addProfile()">
          <ha-icon icon="mdi:plus"></ha-icon>
          Neues Profil
        </button>
        <div class="toolbar-actions">
          <button class="btn btn-secondary" onclick="window.shutterpilotCard._callService('all_up')">
            <ha-icon icon="mdi:arrow-up"></ha-icon>
            Alle hoch
          </button>
          <button class="btn btn-secondary" onclick="window.shutterpilotCard._callService('all_down')">
            <ha-icon icon="mdi:arrow-down"></ha-icon>
            Alle runter
          </button>
          <button class="btn btn-secondary" onclick="window.shutterpilotCard._callService('stop')">
            <ha-icon icon="mdi:stop"></ha-icon>
            Stopp
          </button>
        </div>
      </div>

      <div class="profile-table">
        <div class="table-header">
          <div class="th th-checkbox">
            <input type="checkbox" onclick="window.shutterpilotCard._toggleAll(this)">
          </div>
          <div class="th th-status">Status</div>
          <div class="th th-name">Name</div>
          <div class="th th-cover">Rolllade</div>
          <div class="th th-area">Bereich</div>
          <div class="th th-sensors">Sensoren</div>
          <div class="th th-actions">Aktionen</div>
        </div>

        ${this._profiles.map((profile, index) => `
          <div class="table-row ${profile.enabled ? '' : 'disabled'}">
            <div class="td td-checkbox">
              <input type="checkbox" data-index="${index}">
            </div>
            <div class="td td-status">
              <span class="status-badge status-${profile.status}">
                ${this._getStatusText(profile.status)}
              </span>
            </div>
            <div class="td td-name">
              <strong>${profile.name}</strong>
            </div>
            <div class="td td-cover">
              <code>${profile.cover}</code>
            </div>
            <div class="td td-area">
              <span class="area-badge">
                ${this._areas[profile.area]?.name || 'Kein Bereich'}
              </span>
            </div>
            <div class="td td-sensors">
              <div class="sensor-icons">
                ${profile.window_sensor ? '<ha-icon icon="mdi:window-open" title="Fenster"></ha-icon>' : ''}
                ${profile.door_sensor ? '<ha-icon icon="mdi:door-open" title="Tür"></ha-icon>' : ''}
                ${profile.lux_sensor ? '<ha-icon icon="mdi:brightness-5" title="Helligkeit"></ha-icon>' : ''}
                ${profile.temp_sensor ? '<ha-icon icon="mdi:thermometer" title="Temperatur"></ha-icon>' : ''}
              </div>
            </div>
            <div class="td td-actions">
              <button class="action-btn" onclick="window.shutterpilotCard._showInfo(${index})" title="Info">
                <ha-icon icon="mdi:information"></ha-icon>
              </button>
              <button class="action-btn" onclick="window.shutterpilotCard._editProfile(${index})" title="Bearbeiten">
                <ha-icon icon="mdi:pencil"></ha-icon>
              </button>
              <button class="action-btn" onclick="window.shutterpilotCard._copyProfile(${index})" title="Kopieren">
                <ha-icon icon="mdi:content-copy"></ha-icon>
              </button>
              <button class="action-btn action-delete" onclick="window.shutterpilotCard._deleteProfile(${index})" title="Löschen">
                <ha-icon icon="mdi:delete"></ha-icon>
              </button>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  _renderAreasTab() {
    return `
      <div class="areas-grid">
        ${Object.entries(this._areas).map(([key, area]) => `
          <div class="area-card">
            <div class="area-header">
              <h3>${area.name}</h3>
              <button class="btn-icon" onclick="window.shutterpilotCard._editArea('${key}')">
                <ha-icon icon="mdi:pencil"></ha-icon>
              </button>
            </div>
            <div class="area-info">
              <div class="info-row">
                <span class="label">Modus:</span>
                <span class="value">${this._getModeText(area.mode)}</span>
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
                <span class="label">Zugeordnete Profile:</span>
                <span class="value badge">${this._profiles.filter(p => p.area === key).length}</span>
              </div>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  _renderGlobalTab() {
    const globalAuto = this._hass.states[this._config.entity];
    return `
      <div class="global-settings">
        <div class="setting-card">
          <div class="setting-header">
            <h3>Globale Automatik</h3>
            <ha-switch 
              .checked="${globalAuto?.state === 'on'}"
              onclick="window.shutterpilotCard._toggleGlobalAuto(this)">
            </ha-switch>
          </div>
          <p class="setting-description">
            Aktiviert oder deaktiviert die automatische Steuerung aller Rollläden
          </p>
        </div>

        <div class="setting-card">
          <h3>Services</h3>
          <div class="service-buttons">
            <button class="btn btn-block" onclick="window.shutterpilotCard._callService('recalculate_now')">
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
              <span class="value">01.05.</span>
            </div>
            <div class="info-item">
              <span class="label">Ende:</span>
              <span class="value">30.09.</span>
            </div>
          </div>
        </div>

        <div class="setting-card">
          <h3>Standard-Werte</h3>
          <div class="info-grid">
            <div class="info-item">
              <span class="label">Lüftungsposition:</span>
              <span class="value">30%</span>
            </div>
            <div class="info-item">
              <span class="label">Cooldown:</span>
              <span class="value">120s</span>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  _renderEditDialog() {
    return `
      <div class="dialog-overlay" onclick="window.shutterpilotCard._closeDialog()">
        <div class="dialog" onclick="event.stopPropagation()">
          <div class="dialog-header">
            <h2>${this._editingProfile ? 'Profil bearbeiten' : 'Neues Profil'}</h2>
            <button class="btn-icon" onclick="window.shutterpilotCard._closeDialog()">
              <ha-icon icon="mdi:close"></ha-icon>
            </button>
          </div>

          <div class="dialog-tabs">
            <button class="dialog-tab active">Basis</button>
            <button class="dialog-tab">Sensoren</button>
            <button class="dialog-tab">Sonnenschutz</button>
            <button class="dialog-tab">Erweitert</button>
          </div>

          <div class="dialog-content">
            <form id="profile-form">
              <!-- Wird dynamisch gefüllt -->
              <div class="form-group">
                <label>Profilname</label>
                <input type="text" name="name" required>
              </div>
              <!-- Mehr Felder hier -->
            </form>
          </div>

          <div class="dialog-footer">
            <button class="btn btn-secondary" onclick="window.shutterpilotCard._closeDialog()">
              Abbrechen
            </button>
            <button class="btn btn-primary" onclick="window.shutterpilotCard._saveProfile()">
              Speichern
            </button>
          </div>
        </div>
      </div>
    `;
  }

  _getStyles() {
    return `
      :host {
        display: block;
      }

      * {
        box-sizing: border-box;
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
        margin: 0;
        font-size: 24px;
        font-weight: 600;
      }

      .subtitle {
        font-size: 12px;
        opacity: 0.9;
        margin-left: 12px;
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
        min-height: 400px;
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

      .table-row:hover {
        background: var(--primary-background-color, #f9fafb);
      }

      .table-row.disabled {
        opacity: 0.5;
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

      .td-cover code {
        background: var(--secondary-background-color, #f3f4f6);
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-family: monospace;
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

      /* Action Buttons */
      .action-btn {
        background: transparent;
        border: none;
        padding: 6px;
        cursor: pointer;
        border-radius: 6px;
        color: var(--secondary-text-color, #6b7280);
        transition: all 0.2s;
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
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
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
      }

      .area-header h3 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
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

      .badge {
        background: var(--primary-color, #3b82f6);
        color: white;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 11px;
      }

      /* Global Settings */
      .global-settings {
        max-width: 800px;
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
        margin: 0;
        font-size: 18px;
        font-weight: 600;
      }

      .setting-description {
        margin: 0;
        font-size: 14px;
        color: var(--secondary-text-color, #6b7280);
      }

      .info-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
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

      /* Dialog */
      .dialog-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        padding: 20px;
      }

      .dialog {
        background: white;
        border-radius: 16px;
        max-width: 800px;
        width: 100%;
        max-height: 90vh;
        display: flex;
        flex-direction: column;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
      }

      .dialog-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 24px;
        border-bottom: 1px solid var(--divider-color, #e5e7eb);
      }

      .dialog-header h2 {
        margin: 0;
        font-size: 20px;
        font-weight: 600;
      }

      .dialog-tabs {
        display: flex;
        border-bottom: 1px solid var(--divider-color, #e5e7eb);
        padding: 0 24px;
      }

      .dialog-tab {
        padding: 12px 20px;
        border: none;
        background: transparent;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        color: var(--secondary-text-color, #6b7280);
        border-bottom: 2px solid transparent;
        transition: all 0.2s;
      }

      .dialog-tab.active {
        color: var(--primary-color, #3b82f6);
        border-bottom-color: var(--primary-color, #3b82f6);
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
        border-top: 1px solid var(--divider-color, #e5e7eb);
      }

      .btn-block {
        width: 100%;
      }

      .form-group {
        margin-bottom: 20px;
      }

      .form-group label {
        display: block;
        margin-bottom: 8px;
        font-size: 14px;
        font-weight: 500;
        color: var(--primary-text-color);
      }

      .form-group input,
      .form-group select {
        width: 100%;
        padding: 10px 12px;
        border: 1px solid var(--divider-color, #e5e7eb);
        border-radius: 8px;
        font-size: 14px;
        font-family: inherit;
      }

      .form-group input:focus,
      .form-group select:focus {
        outline: none;
        border-color: var(--primary-color, #3b82f6);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
      }

      @media (max-width: 768px) {
        .table-header {
          display: none;
        }

        .table-row {
          flex-direction: column;
          align-items: stretch;
        }

        .th, .td {
          width: 100% !important;
          flex: none !important;
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

  _attachEventListeners() {
    // Global reference für onclick Handler
    window.shutterpilotCard = this;
  }

  _setTab(tab) {
    this._activeTab = tab;
    this.render();
  }

  _addProfile() {
    this._editingProfile = null;
    this.render();
  }

  _editProfile(index) {
    this._editingProfile = this._profiles[index];
    this.render();
  }

  _copyProfile(index) {
    const profile = { ...this._profiles[index], name: `${this._profiles[index].name} (Kopie)` };
    this._profiles.push(profile);
    this.render();
  }

  _deleteProfile(index) {
    if (confirm(`Profil "${this._profiles[index].name}" wirklich löschen?`)) {
      this._profiles.splice(index, 1);
      this.render();
    }
  }

  _closeDialog() {
    this._editingProfile = null;
    this.render();
  }

  _saveProfile() {
    // TODO: Implementiere Save-Logik
    this._closeDialog();
  }

  async _callService(service) {
    if (!this._hass) return;
    
    try {
      await this._hass.callService('shutterpilot', service, {});
      this._showToast(`Service ${service} ausgeführt`);
    } catch (err) {
      this._showToast(`Fehler: ${err.message}`, 'error');
    }
  }

  async _toggleGlobalAuto(element) {
    if (!this._hass) return;
    
    const service = element.checked ? 'turn_on' : 'turn_off';
    await this._hass.callService('switch', service, {
      entity_id: this._config.entity
    });
  }

  _showToast(message, type = 'info') {
    // TODO: Implementiere Toast-Notifications
    console.log(`[${type}] ${message}`);
  }

  _getStatusText(status) {
    const texts = {
      active: 'Aktiv',
      inactive: 'Inaktiv',
      cooldown: 'Cooldown'
    };
    return texts[status] || status;
  }

  _getModeText(mode) {
    const texts = {
      time_only: 'Nur Zeit',
      sun: 'Sonnenstand',
      golden_hour: 'Golden Hour'
    };
    return texts[mode] || mode;
  }

  getCardSize() {
    return 8;
  }
}

customElements.define('shutterpilot-card', ShutterPilotCard);

// Registriere Card in Lovelace
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'shutterpilot-card',
  name: 'ShutterPilot Card',
  description: 'Professional management card for ShutterPilot',
  preview: true,
  documentationURL: 'https://github.com/fschube/shutterpilot'
});

console.info(
  '%c  SHUTTERPILOT-CARD  \n%c  Version 1.0.0       ',
  'color: white; background: #3b82f6; font-weight: 700;',
  'color: #3b82f6; font-weight: 300;'
);

