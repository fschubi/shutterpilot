# ShutterPilot

HACS Integration für intelligente, sensorbasierte Rollladensteuerung für Home Assistant mit automatischer Beschattung, Fenster-/Türüberwachung und Cooldown-Logik.

## Features

✅ **Vollautomatische Steuerung** basierend auf:
- 🌞 Sonnenstand (Azimut & Elevation)
- 🌡️ Temperatur- und Helligkeitssensoren
- 🪟 Fenster- und Türkontakten
- ⏰ Zeitplänen und Tageslichtlogik
- ❄️ Cooldown-System zur Vermeidung unnötiger Bewegungen

✅ **Mehrere Profile** pro Integration - jeder Rollladen individuell konfigurierbar  
✅ **Manuelle Steuerung** bleibt jederzeit möglich  
✅ **Zentrale Konfiguration** über Home Assistant UI (ConfigFlow)  
✅ **Services** für globale Aktionen (alle hoch/runter, Stopp, Neuberechnung)

## Installation (HACS)

1. HACS öffnen → **Custom repositories**
2. Repository hinzufügen: `https://github.com/fschube/shutterpilot` (Kategorie: **Integration**)
3. HACS → **Integrations** → **ShutterPilot** installieren
4. Home Assistant neu starten
5. **Einstellungen** → **Geräte & Dienste** → **Integrationen** → **ShutterPilot** hinzufügen

## Konfiguration

### Initial Setup

Bei der ersten Einrichtung werden globale Standardwerte festgelegt:
- **Automatik global aktiv**: Master-Schalter für alle Profile
- **Standard Lüftungsposition**: Position bei geöffnetem Fenster (0-80%)
- **Standard Cooldown**: Wartezeit nach Fensterschließung (0-900 Sekunden)

### Profile erstellen

Über **Optionen** der Integration können Profile hinzugefügt werden. Jedes Profil benötigt:

**Pflichtfelder:**
- **Name**: Bezeichnung des Profils
- **Cover Entity**: Rollladen-Entity (z.B. `cover.wohnzimmer_rollladen`)

**Optionale Sensoren:**
- **Fenster-Sensor**: Binary Sensor für Fensterkontakt
- **Tür-Sensor**: Binary Sensor für Türkontakt
- **Lux-Sensor**: Helligkeitssensor
- **Temperatur-Sensor**: Temperatursensor

**Positionen:**
- **Tag-Position**: Position bei Beschattungsbedarf (default: 40%)
- **Nacht-Position**: Position nachts (default: 0%)
- **Lüftungsposition**: Position bei geöffnetem Fenster
- **Tür-Sicherheitsposition**: Mindestposition bei geöffneter Tür

**Beschattungslogik:**
- **Lux-Schwellwert**: Ab diesem Wert wird beschattet (default: 20000)
- **Temperatur-Schwellwert**: Ab diesem Wert wird beschattet (default: 26°C)
- **Azimut-Min/Max**: Sonnenstand-Bereich für Beschattung (-360 bis 360°)

**Zeitpläne:**
- **Up-Time**: Fester Zeitpunkt zum Öffnen (Format: HH:MM)
- **Down-Time**: Fester Zeitpunkt zum Schließen (Format: HH:MM)

**Erweitert:**
- **Cooldown**: Individuelle Wartezeit nach Fensterschließung (0-1800 Sekunden)
- **Aktiviert**: Profil kann temporär deaktiviert werden

## Services

Die Integration stellt folgende Services bereit:

### `shutterpilot.all_up`
Alle konfigurierten Rollläden öffnen.

### `shutterpilot.all_down`
Alle Rollläden herunterfahren (unter Berücksichtigung von Fenster-/Türlogik).

### `shutterpilot.stop`
Alle Rollläden stoppen.

### `shutterpilot.recalculate_now`
Sofortige Neuberechnung aller Profile (umgeht Cooldown).

## Entscheidungslogik

Die Steuerung folgt folgender Priorität:

1. **Tür offen** → Tür-Sicherheitsposition (höchste Position)
2. **Fenster offen** → Lüftungsposition
3. **Cooldown aktiv** → Keine Aktion
4. **Zeitplan-Match** → Entsprechend öffnen/schließen
5. **Sonnenstand + Sensoren** → Beschattung bei Bedarf oder öffnen
6. **Nacht** → Nacht-Position

## UI Entities

Die Integration erstellt automatisch:

- **Switch**: `switch.shutterpilot_automatik_global` - Globale Automatik ein/aus
- **Number**: `number.shutterpilot_standard_lueftungsposition` - Standard Lüftungsposition (0-80%)

## Versionshistorie

- **0.2.6**: Vollständige Implementierung mit Profil-System, Sensoren, Cooldown-Logik
- **0.1.0**: Grundgerüst (Config-Flow, globaler Auto-Switch)

## Support

- **Issues**: [GitHub Issues](https://github.com/fschube/shutterpilot/issues)
- **Dokumentation**: [GitHub Repository](https://github.com/fschube/shutterpilot)

## Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei.
