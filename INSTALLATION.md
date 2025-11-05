# ShutterPilot v0.3.0 - Installations- und Setup-Anleitung

## 📋 Inhaltsverzeichnis

1. [Voraussetzungen](#voraussetzungen)
2. [Installation](#installation)
3. [Erste Einrichtung](#erste-einrichtung)
4. [Management Card installieren](#management-card-installieren)
5. [Bereiche konfigurieren](#bereiche-konfigurieren)
6. [Profile erstellen](#profile-erstellen)
7. [Erweiterte Features nutzen](#erweiterte-features-nutzen)
8. [Troubleshooting](#troubleshooting)

---

## Voraussetzungen

- **Home Assistant** Version 2023.1 oder höher
- **HACS** (Home Assistant Community Store) installiert
- **Rollläden** (Cover-Entities) in Home Assistant eingerichtet
- **Optional**: Sensoren für Fenster, Türen, Helligkeit, Temperatur

---

## Installation

### Schritt 1: Repository zu HACS hinzufügen

1. Öffne **HACS** in Home Assistant
2. Klicke auf die **3 Punkte** oben rechts
3. Wähle **Custom repositories**
4. Füge hinzu:
   - **Repository**: `https://github.com/fschube/shutterpilot`
   - **Kategorie**: `Integration`
5. Klicke **Hinzufügen**

### Schritt 2: ShutterPilot installieren

1. HACS → **Integrations**
2. Suche nach **"ShutterPilot"**
3. Klicke **Download**
4. Wähle **Version v0.3.0** (oder neuer)
5. Klicke **Download**

### Schritt 3: Home Assistant neu starten

1. **Einstellungen** → **System** → **Neu starten**
2. Warte bis HA vollständig neu gestartet ist

---

## Erste Einrichtung

### Integration hinzufügen

1. **Einstellungen** → **Geräte & Dienste**
2. Klicke **Integration hinzufügen** (unten rechts)
3. Suche nach **"ShutterPilot"**
4. Konfiguriere die globalen Einstellungen:

```
┌─────────────────────────────────────────┐
│ Globale Einstellungen                    │
├─────────────────────────────────────────┤
│ ☑ Automatik global aktiv               │
│                                         │
│ Standard Lüftungsposition: [30] %      │
│ (Position bei geöffnetem Fenster)      │
│                                         │
│ Standard Cooldown: [120] Sekunden      │
│ (Wartezeit nach manueller Bedienung)   │
└─────────────────────────────────────────┘
```

5. Klicke **Absenden**

✅ **Fertig!** ShutterPilot ist jetzt aktiv.

---

## Management Card installieren

Die **Management Card** bietet eine professionelle Oberfläche zur Verwaltung aller Profile.

### Schritt 1: Ressource hinzufügen

1. **Einstellungen** → **Dashboards**
2. Klicke auf die **3 Punkte** oben rechts
3. Wähle **Ressourcen**
4. Klicke **Ressource hinzufügen** (unten rechts)
5. Konfiguriere:
   - **URL**: `/local/community/shutterpilot/shutterpilot-card.js`
   - **Ressourcentyp**: `JavaScript-Modul`
6. Klicke **Erstellen**

### Schritt 2: Karte zum Dashboard hinzufügen

1. Öffne dein **Dashboard**
2. Klicke **Bearbeiten** (oben rechts)
3. Klicke **Karte hinzufügen**
4. Suche nach **"shutterpilot"** oder wähle **Manuell**
5. Füge folgende YAML ein:

```yaml
type: custom:shutterpilot-card
entity: switch.shutterpilot_global_automation
```

6. Klicke **Speichern**

✅ **Fertig!** Die Management Card wird angezeigt.

### Alternative: Erweiterte Konfiguration

```yaml
type: custom:shutterpilot-card
entity: switch.shutterpilot_global_automation
title: Rollladensteuerung
show_toolbar: true
```

---

## Bereiche konfigurieren

Bereiche sind **Zeit-Templates** für mehrere Rollläden.

### Via Config Flow

1. **Geräte & Dienste** → **ShutterPilot** → **Konfigurieren**
2. Wähle **"Bereiche verwalten"**
3. Wähle einen Bereich (Wohn/Schlaf/Kinder)
4. Konfiguriere:

```
┌─────────────────────────────────────────┐
│ Bereich: Wohnbereich                     │
├─────────────────────────────────────────┤
│ Name: [Wohnbereich]                     │
│                                         │
│ Modus: [Sonnenstand ▼]                 │
│ • Nur Zeit                              │
│ • Sonnenstand                           │
│ • Golden Hour                           │
│                                         │
│ ─────── Wochentag ───────              │
│ Hochfahrzeit:     [06:30]              │
│ Runterfahrzeit:   [22:00]              │
│                                         │
│ ─────── Wochenende ──────               │
│ Hochfahrzeit:     [08:00]              │
│ Runterfahrzeit:   [23:00]              │
│                                         │
│ ─────── Grenzen ─────────               │
│ Früheste Hochfahrzeit: [06:00]         │
│ Späteste Hochfahrzeit: [09:00]         │
│                                         │
│ Verzögerung: [10] Sekunden             │
└─────────────────────────────────────────┘
```

5. Klicke **Absenden**

### Modi erklärt

**Nur Zeit:**
- Rollläden fahren zu festen Zeiten
- Keine Sonnenstandsberechnung

**Sonnenstand:**
- Hochfahren: Bei Sonnenaufgang (aber nicht vor "Früheste Zeit")
- Runterfahren: Bei Sonnenuntergang (aber nicht nach "Runterfahrzeit")

**Golden Hour:**
- Wie Sonnenstand, aber mit Golden Hour
- Ca. 1 Stunde vor Sonnenuntergang / nach Sonnenaufgang

---

## Profile erstellen

Profile steuern **einzelne Rollläden**.

### Via Management Card (Empfohlen)

1. Öffne die **ShutterPilot Card**
2. Klicke **"Neues Profil"**
3. Fülle die Tabs aus:

#### Tab: Basis
```
Name: Wohnzimmer Südfenster
Cover: cover.wohnzimmer_rollade
Bereich: Wohnbereich
```

#### Tab: Sensoren
```
Fenster-Sensor: binary_sensor.fenster_wohnzimmer
Tür-Sensor: (leer)
Lux-Sensor: sensor.brightness_outside
Temperatur-Sensor: sensor.temperature_wohnzimmer
```

#### Tab: Sonnenschutz
```
Lux-Schwellwert: 20000 lx
Lux-Hysterese: 20%

Temperatur-Schwellwert: 26°C
Temperatur-Hysterese: 10%

Azimut Min: 100°
Azimut Max: 250°
```

#### Tab: Erweitert
```
Fenster öffnen Verzögerung: 5 Sekunden
Fenster schließen Verzögerung: 30 Sekunden

☑ Wärmeschutz aktivieren
Wärmeschutz-Temperatur: 30°C

☑ Im Sonnenschutz halten
```

4. Klicke **Speichern**

### Via Config Flow

1. **Geräte & Dienste** → **ShutterPilot** → **Konfigurieren**
2. Wähle **"Neues Profil hinzufügen"**
3. Folge dem Assistenten (alle Felder wie oben)

---

## Erweiterte Features nutzen

### Feature 1: Hysterese (Anti-Flacker)

**Problem**: Bei schwankenden Sensorwerten fährt der Rollladen ständig hoch/runter.

**Lösung**: Hysterese einschalten

```
Lux-Schwellwert: 20000 lx
Lux-Hysterese: 20%

Verhalten:
• Aktiviert bei: ≥ 20000 lx
• Deaktiviert bei: < 16000 lx (20% unter Schwellwert)
```

---

### Feature 2: Fenster-Verzögerungen

**Use Case**: Kurzes Lüften soll Rollladen nicht hochfahren.

```
Fenster öffnen Verzögerung: 30 Sekunden
→ Rollladen fährt erst hoch wenn Fenster >30s offen

Fenster schließen Verzögerung: 10 Sekunden
→ Rollladen fährt erst runter wenn Fenster >10s geschlossen
```

---

### Feature 3: Zwischenposition (Weihnachten)

**Use Case**: Schwibbögen sollen sichtbar bleiben, aber später vollständig schließen.

```
Zwischenposition: 40%
Zwischenzeit: 17:00
Runterfahrzeit: 22:00

Verhalten:
17:00 → Rollladen auf 40%
22:00 → Rollladen auf 0% (geschlossen)
```

---

### Feature 4: Wärmeschutz

**Use Case**: Bei extremer Hitze vollständig schließen.

```
☑ Wärmeschutz aktivieren
Wärmeschutz-Temperatur: 30°C

Verhalten:
< 30°C → Normale Beschattungsposition (z.B. 20%)
≥ 30°C → Vollständig geschlossen (0%)
```

---

### Feature 5: Im Sonnenschutz halten

**Use Case**: Rollladen soll nicht mehrfach am Tag hoch/runter fahren.

```
☑ Im Sonnenschutz halten

Verhalten:
• Sonnenschutz aktiv → Rollladen runter
• Sonnenschutz inaktiv → Rollladen bleibt unten!
• Erst am Abend (Runterfahrzeit) wird neu evaluiert
```

Besonders praktisch bei **Jalousien** (Lamellen bleiben geschlossen).

---

### Feature 6: Sommer-Ausnahme

**Use Case**: Nord-Fenster brauchen keine Beschattung im Sommer.

**Global konfigurieren:**
1. **Geräte & Dienste** → **ShutterPilot** → **Konfigurieren**
2. **Global-Einstellungen bearbeiten**
3. Sommerzeitraum festlegen:
   ```
   Sommer Beginn: 01.05.
   Sommer Ende: 30.09.
   ```

**Pro Profil aktivieren:**
```
☑ Im Sommer nicht schließen

Verhalten:
01.05. - 30.09. → Rollladen fährt NICHT automatisch runter
```

---

## Troubleshooting

### Problem: Profile werden beim HA-Start nicht geladen

**Symptom**: "Cover entity not found" beim Start

**Ursache**: Race-Condition - ShutterPilot startet vor der Cover-Integration

**Lösung**: 
- Warte ca. 1-2 Minuten nach HA-Start
- Profile validieren Entities zur Laufzeit
- Funktioniert automatisch sobald alle Entities geladen sind

---

### Problem: Management Card zeigt nicht an

**Symptom**: Karte erscheint nicht im Dashboard

**Lösung**:
1. Prüfe **Ressource**:
   - Einstellungen → Dashboards → Ressourcen
   - URL korrekt: `/local/community/shutterpilot/shutterpilot-card.js`
   - Typ: `JavaScript-Modul`

2. **Browser-Cache leeren**:
   - Chrome/Edge: `Strg + Shift + R`
   - Firefox: `Strg + F5`

3. **Browser-Konsole prüfen**:
   - Drücke `F12`
   - Tab "Console" öffnen
   - Fehler suchen

---

### Problem: Rollläden fahren nicht automatisch

**Prüfungen:**

1. **Globale Automatik aktiv?**
   ```
   switch.shutterpilot_global_automation → ON
   ```

2. **Profil-Automatik aktiv?**
   ```
   switch.shutterpilot_wohnzimmer_automation → ON
   ```

3. **Profil im Cooldown?**
   ```
   sensor.shutterpilot_wohnzimmer_status → "cooldown"
   ```
   Warte bis Cooldown abgelaufen ist.

4. **Fenster/Tür offen?**
   - Prüfe Aussperrschutz-Einstellungen
   - Prüfe Sensor-Status

---

### Problem: Beschattung funktioniert nicht

**Prüfungen:**

1. **Sensoren konfiguriert?**
   - Lux-Sensor: `sensor.brightness_outside`
   - Temp-Sensor: `sensor.temperature_xyz`

2. **Schwellwerte erreicht?**
   ```
   sensor.brightness_outside ≥ Lux-Schwellwert
   sensor.temperature_xyz ≥ Temp-Schwellwert
   ```

3. **Sonnenwinkel im Bereich?**
   ```
   sensor.shutterpilot_xyz_sun_elevation
   → Attribute: Azimut prüfen
   ```

4. **Globale Sonnenhöhe-Ende nicht unterschritten?**
   - Einstellungen → ShutterPilot → Global
   - "Sonnenhöhe-Ende" prüfen

---

## 🎓 Nächste Schritte

1. ✅ **Bereiche konfigurieren** für deine Wohnung
2. ✅ **Profile erstellen** für jeden Rollladen
3. ✅ **Sensoren zuordnen** (Fenster, Lux, Temp)
4. ✅ **Erweiterte Features** aktivieren (Hysterese, Verzögerungen)
5. ✅ **Management Card** nutzen für einfache Verwaltung

---

## 💬 Fragen?

- 📖 **Dokumentation**: [README.md](README.md)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/fschube/shutterpilot/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/fschube/shutterpilot/discussions)

**Viel Spaß mit ShutterPilot v0.3.0! 🚀**

