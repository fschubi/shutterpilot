# ShutterPilot v0.3.0 - Enterprise Rollladensteuerung

🎯 **Professional** HACS Integration für intelligente, sensorbasierte Rollladensteuerung für Home Assistant.

## ⭐ Features v0.3.0

### 🏠 **Bereichs-Management (NEU!)**
- ✅ **3 vordefinierte Bereiche**: Wohn-, Schlaf- und Kinderbereich
- ✅ **Zeit-Templates pro Bereich** mit Wochentag/Wochenende
- ✅ **3 Steuerungsarten**: Nur Zeit, Sonnenstand, Golden Hour
- ✅ **Profile automatisch zuordnen** (übernehmen Bereichs-Zeiten)

### 📊 **Professional Management Card (NEU!)**
- ✅ **Tabellarische Übersicht** aller Profile
- ✅ **Schnellaktionen**: Bearbeiten, Kopieren, Löschen
- ✅ **Status-Anzeige** pro Profil (Aktiv/Inaktiv/Cooldown)
- ✅ **Tab-Navigation**: Profile, Bereiche, Global
- ✅ **Modern & Responsive** Design

### 🚀 **Erweiterte Automatisierung**
- ✅ **Hysterese für Sensoren** - Verhindert Flackern (0-100%)
- ✅ **Fenster-Verzögerungen** - Delays beim Öffnen/Schließen
- ✅ **Zwischenposition** - Z.B. für Weihnachtsbeleuchtung
- ✅ **Wärmeschutz** - Vollständiges Schließen bei Hitze
- ✅ **Im Sonnenschutz halten** - Rollladen bleibt bis zum Abend
- ✅ **Sommer-Ausnahme** - Nicht schließen im Sommer

### 💡 **Basis-Features**
- 🌞 **Sonnenstand-basiert** (Azimut & Elevation)
- 🌡️ **Temperatur- und Helligkeitssensoren**
- 🪟 **Fenster- und Türüberwachung**
- ⏰ **Zeitpläne und Golden Hour**
- ❄️ **Cooldown-System**
- 🔧 **Profil-spezifische Switches & Sensoren**
- 🎛️ **Services** für globale Aktionen

---

## 📦 Installation

### 1. HACS Installation

1. HACS öffnen → **Custom repositories**
2. Repository hinzufügen: `https://github.com/fschube/shutterpilot` (Kategorie: **Integration**)
3. HACS → **Integrations** → **ShutterPilot** installieren
4. Home Assistant neu starten

### 2. Integration einrichten

1. **Einstellungen** → **Geräte & Dienste** → **Integrationen**
2. **Integration hinzufügen** → "ShutterPilot" suchen
3. Globale Einstellungen konfigurieren:
   - Automatik global aktiv
   - Standard Lüftungsposition (0-80%)
   - Standard Cooldown (0-900 Sekunden)

### 3. Management Card installieren (Optional aber empfohlen!)

#### Schritt 1: Ressource hinzufügen

1. **Einstellungen** → **Dashboards** → **⋮ Menü** → **Ressourcen**
2. **Ressource hinzufügen**:
   - **URL**: `/local/community/shutterpilot/shutterpilot-card.js`
   - **Ressourcentyp**: JavaScript-Modul
3. **Erstellen** klicken

#### Schritt 2: Karte hinzufügen

1. Dashboard öffnen → **Bearbeiten**
2. **Karte hinzufügen** → **Benutzerdefiniert: ShutterPilot Card**
3. Konfiguration:

```yaml
type: custom:shutterpilot-card
entity: switch.shutterpilot_global_automation
```

#### Alternative: Manuelle YAML-Konfiguration

```yaml
type: custom:shutterpilot-card
entity: switch.shutterpilot_global_automation
title: ShutterPilot Management  # Optional
show_toolbar: true              # Optional, default: true
```

---

## ⚙️ Konfiguration

### Bereiche konfigurieren

1. **Geräte & Dienste** → **ShutterPilot** → **Konfigurieren**
2. **Bereiche verwalten** auswählen
3. Bereich bearbeiten (Wohn/Schlaf/Kinder):
   - **Name**: Bezeichnung des Bereichs
   - **Modus**: Zeit / Sonnenstand / Golden Hour
   - **Zeiten Wochentag**: Hoch-/Runterfahrzeit (HH:MM)
   - **Zeiten Wochenende**: Hoch-/Runterfahrzeit (HH:MM)
   - **Früheste Hochfahrzeit**: Nicht vor dieser Zeit
   - **Späteste Hochfahrzeit**: Spätestens zu dieser Zeit
   - **Verzögerung**: Sekunden zwischen Rollläden (0-300)

### Profile erstellen

#### Via Management Card (Empfohlen):
1. Öffne die ShutterPilot Card
2. Klicke **"Neues Profil"**
3. Fülle die Tabs aus:
   - **Basis**: Name, Cover, Bereich
   - **Sensoren**: Fenster, Tür, Lux, Temperatur
   - **Sonnenschutz**: Schwellwerte, Azimut, Hysterese
   - **Erweitert**: Verzögerungen, Wärmeschutz, etc.

#### Via Config Flow:
1. **Geräte & Dienste** → **ShutterPilot** → **Konfigurieren**
2. **Aktion**: "Neues Profil hinzufügen"

**Basis-Einstellungen:**
- ✅ **Name**: Bezeichnung des Profils
- ✅ **Cover Entity**: Rollladen-Entity (`cover.xyz`)
- ✅ **Bereich zuordnen**: Wohn/Schlaf/Kinder/Keiner

**Sensoren (Optional):**
- 🪟 **Fenster-Sensor**: Binary Sensor für Fensterkontakt
- 🚪 **Tür-Sensor**: Binary Sensor für Türkontakt
- ☀️ **Lux-Sensor**: Helligkeitssensor (mit Device-Class `illuminance`)
- 🌡️ **Temperatur-Sensor**: Temperatursensor (mit Device-Class `temperature`)

**Positionen:**
- **Tagesposition**: 0-100% (Standard: 40%)
- **Nachtposition**: 0-100% (Standard: 0%)
- **Lüftungsposition**: 0-80% (bei offenem Fenster)
- **Sichere Tür-Position**: 0-80% (bei offener Tür)

**Sonnenschutz:**
- **Helligkeits-Schwellwert**: Z.B. 20000 lx
- **Helligkeits-Hysterese**: 0-100% (verhindert Flackern)
- **Temperatur-Schwellwert**: Z.B. 26°C
- **Temperatur-Hysterese**: 0-100%
- **Azimut Min/Max**: Sonnenwinkel (-360° bis 360°)

**Erweiterte Features:**
- ⏱️ **Fenster öffnen Verzögerung**: 0-300 Sekunden
- ⏱️ **Fenster schließen Verzögerung**: 0-300 Sekunden
- 🎄 **Zwischenposition**: 0-100% (z.B. für Weihnachten)
- 🎄 **Zwischenzeit**: HH:MM
- 🔥 **Wärmeschutz**: Bei Hitze vollständig schließen
- 🔥 **Wärmeschutz-Temperatur**: Z.B. 30°C
- 🌞 **Im Sonnenschutz halten**: Bis zum Abend
- ☀️ **Helligkeits-Ende Verzögerung**: 0-60 Minuten
- ☀️ **Im Sommer nicht schließen**: Verwendet globalen Sommerzeitraum

**Zeit-Überschreibungen:**
- **Hochfahrzeit**: HH:MM (überschreibt Bereichszeit)
- **Runterfahrzeit**: HH:MM (überschreibt Bereichszeit)

**Licht-Automation:**
- 💡 **Licht-Entity**: Light Entity (`light.xyz`)
- 💡 **Helligkeit**: 0-100%
- 💡 **Bei Beschattung**: Licht einschalten
- 💡 **Bei Nacht**: Licht einschalten

---

## 🎮 Verwendung

### Via Management Card

Die **ShutterPilot Card** bietet eine übersichtliche Oberfläche:

#### **Profile-Tab:**
- Tabellarische Übersicht aller Profile
- Status-Anzeige (Aktiv/Inaktiv/Cooldown)
- Sensor-Icons (Fenster/Tür/Lux/Temp)
- Aktionen: Info, Bearbeiten, Kopieren, Löschen
- Schnellaktionen: Alle hoch/runter/stopp

#### **Bereiche-Tab:**
- Übersicht aller 3 Bereiche
- Zeiten und Modus pro Bereich
- Anzahl zugeordneter Profile
- Bereich bearbeiten

#### **Global-Tab:**
- Globale Automatik ein/aus
- Services ausführen
- Sommerzeitraum anzeigen
- Standard-Werte einsehen

### Entities

Nach der Einrichtung werden automatisch erstellt:

#### **Switches:**
- `switch.shutterpilot_global_automation` - Master-Schalter
- `switch.shutterpilot_<profil>_automation` - Pro Profil

#### **Sensors:**
- `sensor.shutterpilot_<profil>_status` - Status (Aktiv/Inaktiv/Cooldown)
- `sensor.shutterpilot_<profil>_last_action` - Letzte Aktion & Grund
- `sensor.shutterpilot_<profil>_cooldown_remaining` - Verbleibender Cooldown (Sekunden)
- `sensor.shutterpilot_<profil>_sun_elevation` - Sonnenhöhe + Attribute (Azimut, Range)

#### **Number:**
- `number.shutterpilot_default_ventilation_position` - Standard Lüftungsposition

### Services

```yaml
# Alle Rollläden öffnen
service: shutterpilot.all_up

# Alle Rollläden schließen (mit Fenster/Tür-Logik)
service: shutterpilot.all_down

# Alle Rollläden stoppen
service: shutterpilot.stop

# Sofortige Neuberechnung (umgeht Cooldown)
service: shutterpilot.recalculate_now
```

---

## 🧩 Beispiel-Automatisierungen

### Globale Automatik bei Abwesenheit deaktivieren

```yaml
automation:
  - alias: "ShutterPilot bei Abwesenheit aus"
    trigger:
      - platform: state
        entity_id: person.home
        to: "not_home"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.shutterpilot_global_automation
```

### Einzelnes Profil zeitweise deaktivieren

```yaml
automation:
  - alias: "Wohnzimmer Rollladen manuell am Wochenende"
    trigger:
      - platform: time
        at: "00:00:00"
    condition:
      - condition: time
        weekday:
          - sat
          - sun
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.shutterpilot_wohnzimmer_automation
```

### Benachrichtigung bei Cooldown

```yaml
automation:
  - alias: "Benachrichtigung Rollladen Cooldown"
    trigger:
      - platform: state
        entity_id: sensor.shutterpilot_wohnzimmer_status
        to: "cooldown"
    action:
      - service: notify.mobile_app
        data:
          message: "Wohnzimmer Rollladen in Cooldown ({{ states('sensor.shutterpilot_wohnzimmer_cooldown_remaining') }}s)"
```

---

## 📸 Screenshots

### Management Card - Profile Tab
![Profile Tab](docs/images/profiles-tab.png)
*Tabellarische Übersicht aller Profile mit Status und Schnellaktionen*

### Management Card - Bereiche Tab
![Bereiche Tab](docs/images/areas-tab.png)
*Übersicht und Verwaltung der 3 Bereiche*

### Management Card - Global Tab
![Global Tab](docs/images/global-tab.png)
*Globale Einstellungen und Services*

---

## 🔧 Technische Details

### Bereichs-Modi

**Nur Zeit:**
- Rollläden fahren zu festen Zeiten
- Keine Sonnenstandsberechnung

**Sonnenstand:**
- Kombination aus Zeit und Sonnenauf-/-untergang
- Rollläden fahren nicht vor frühester/nach spätester Zeit

**Golden Hour:**
- Wie Sonnenstand, aber mit Golden Hour als Referenz
- Ca. 1 Stunde vor Sonnenuntergang / nach Sonnenaufgang

### Hysterese-Logik

Verhindert ständiges Auf-/Abfahren bei schwankenden Sensorwerten:

**Beispiel Lux-Sensor:**
- Schwellwert: 20000 lx
- Hysterese: 20%
- **Aktivierung**: bei ≥ 20000 lx
- **Deaktivierung**: bei < 16000 lx (20% unter Schwellwert)

### Cooldown-System

Nach manuellen Änderungen wird der Cooldown aktiviert:
- Verhindert sofortiges Zurückfahren
- Konfigurierbarer Zeitraum (0-1800 Sekunden)
- Sichtbar im Status-Sensor

---

## 🐛 Troubleshooting

### Profile werden beim HA-Start nicht geladen

**Problem**: "Cover entity not found" beim Start  
**Lösung**: Race-Condition beim HA-Start - Profile validieren Entities zur Laufzeit. Nach vollständigem Start funktioniert es automatisch.

### Management Card zeigt nicht an

**Problem**: Card erscheint nicht im Dashboard  
**Lösung**: 
1. Prüfe ob Ressource korrekt hinzugefügt wurde
2. Lösche Browser-Cache (Strg+Shift+R)
3. Prüfe Browser-Konsole auf Fehler (F12)

### Rollläden fahren nicht automatisch

**Prüfungen:**
1. Globale Automatik aktiv? (`switch.shutterpilot_global_automation`)
2. Profil-Automatik aktiv? (`switch.shutterpilot_<profil>_automation`)
3. Profil im Cooldown? (`sensor.shutterpilot_<profil>_status`)
4. Fenster/Tür offen? (prüfe Aussperrschutz-Einstellungen)

### Beschattung funktioniert nicht

**Prüfungen:**
1. Lux- und/oder Temp-Sensor konfiguriert?
2. Schwellwerte erreicht?
3. Sonnenwinkel im konfigurierten Bereich? (Azimut Min/Max)
4. Sonnenhöhe über globalem Ende-Wert?

---

## 📝 Changelog

### v0.3.0 (2025-01-XX) - Enterprise Release

**🚀 Neue Features:**
- Bereichs-Management (Wohn/Schlaf/Kinder)
- Professional Management Card mit Tabellenansicht
- Golden Hour Support
- Hysterese für Lux/Temperatur-Sensoren
- Fenster-Verzögerungen (öffnen/schließen)
- Zwischenposition mit Zeitsteuerung
- Wärmeschutz (vollständiges Schließen bei Hitze)
- Im Sonnenschutz halten (bis zum Abend)
- Sommer-Ausnahme (nicht schließen im Sommer)
- Helligkeits-Ende Verzögerung
- Licht-Automation (NEU)

**🎨 Verbesserungen:**
- Entity-Selektoren mit Auto-Vervollständigung
- Vollständige deutsche und englische Übersetzungen
- Globale Sonnen-Offsets
- Sommerzeitraum konfigurierbar

---

## 📄 Lizenz

MIT License - Siehe LICENSE Datei

## 🤝 Contributing

Contributions sind willkommen! Bitte erstelle ein Issue oder Pull Request auf GitHub.

## 💬 Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/fschube/shutterpilot/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/fschube/shutterpilot/discussions)
- 📖 **Dokumentation**: [GitHub Wiki](https://github.com/fschube/shutterpilot/wiki)

---

**Made with ❤️ for Home Assistant**
