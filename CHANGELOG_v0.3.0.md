# ShutterPilot v0.3.0 - Enterprise Release 🚀

## 📅 Release Date: Januar 2025

### 🎯 Was ist neu?

Diese Version bringt **ShutterPilot** auf ein völlig neues, professionelles Level - inspiriert von ioBroker's shuttercontrol, aber für Home Assistant optimiert!

---

## 🌟 Hauptfeatures

### 1. 🏠 **Bereichs-Management**

Definiere bis zu **3 globale Bereiche** (Wohn-, Schlaf-, Kinderbereich) mit eigenen Zeit-Templates:

- ✅ **3 Steuerungsarten**: Nur Zeit / Sonnenstand / Golden Hour
- ✅ **Wochentag/Wochenende**: Separate Zeiten konfigurierbar
- ✅ **Früheste/Späteste Zeit**: Nie vor/nach diesen Zeiten fahren
- ✅ **Stagger-Delay**: Zeitversatz zwischen Rollläden (Funk-Entlastung)
- ✅ **Profile automatisch zuordnen**: Übernehmen Bereichs-Zeiten

**Beispiel:**
```
Wohnbereich:
  - Modus: Sonnenstand
  - Woche Hoch: 06:30, Runter: 22:00
  - Wochenende Hoch: 08:00, Runter: 23:00
  - Früheste: 06:00, Späteste: 09:00
  - Verzögerung: 10 Sekunden
```

---

### 2. 📊 **Professional Management Card**

Brandneue Custom Lovelace Card mit **Enterprise-Level UI**:

#### Features:
- ✅ **Tabellarische Übersicht** aller Profile (wie shuttercontrol)
- ✅ **3 Tabs**: Profile / Bereiche / Global
- ✅ **Live Status-Anzeige**: Aktiv / Inaktiv / Cooldown
- ✅ **Sensor-Icons**: Zeigt konfigurierte Sensoren
- ✅ **Schnellaktionen**: 
  - Info anzeigen
  - Profil bearbeiten
  - Profil kopieren
  - Profil löschen
- ✅ **Bulk-Aktionen**: Alle hoch/runter/stopp
- ✅ **Responsive Design**: Funktioniert auf Desktop & Mobile
- ✅ **Modern & Professional**: Home Assistant Design Language

#### Installation:
```yaml
# 1. Ressource hinzufügen
URL: /local/community/shutterpilot/shutterpilot-card.js
Typ: JavaScript-Modul

# 2. Karte im Dashboard
type: custom:shutterpilot-card
entity: switch.shutterpilot_global_automation
```

---

### 3. 🌅 **Golden Hour Support**

Rollläden können nun zur **Golden Hour** fahren:
- Ca. 1 Stunde vor Sonnenuntergang / nach Sonnenaufgang
- Perfekt für sanftere Übergänge
- Pro Bereich konfigurierbar

---

### 4. 📈 **Sensor-Hysterese**

Verhindert ständiges Auf-/Abfahren bei schwankenden Sensorwerten:

**Lux-Hysterese (0-100%):**
- Schwellwert: 20000 lx, Hysterese: 20%
- **Aktiviert** bei: ≥ 20000 lx
- **Deaktiviert** bei: < 16000 lx (20% unter Schwellwert)

**Temperatur-Hysterese (0-100%):**
- Schwellwert: 26°C, Hysterese: 10%
- **Aktiviert** bei: ≥ 26°C
- **Deaktiviert** bei: < 23.4°C (10% unter Schwellwert)

---

### 5. ⏱️ **Fenster/Tür-Verzögerungen**

**Fenster öffnen Verzögerung (0-300s):**
- Rollladen fährt erst nach X Sekunden hoch
- Verhindert Reaktion auf kurzes Lüften

**Fenster schließen Verzögerung (0-300s):**
- Rollladen fährt erst nach X Sekunden runter
- Wartet ab ob Fenster wieder geöffnet wird

---

### 6. 🎄 **Zwischenposition**

Für Weihnachten oder andere Anlässe:

- **Zwischenposition (0-100%)**: Z.B. 50% für Schwibbögen
- **Zwischenzeit (HH:MM)**: Ab wann gilt die Zwischenposition?
- Später am Abend kann mit regulärer Runterfahrzeit vollständig geschlossen werden

**Beispiel:**
```
Zwischenposition: 50%
Zwischenzeit: 18:00
Runterfahrzeit: 22:00

Ergebnis:
18:00 → Rollladen auf 50%
22:00 → Rollladen auf 0% (geschlossen)
```

---

### 7. 🔥 **Wärmeschutz**

Bei extremer Hitze **vollständig schließen**:

- **Wärmeschutz aktivieren**: Checkbox
- **Wärmeschutz-Temperatur**: Z.B. 30°C
- Überschreibt normale Beschattungsposition

---

### 8. 🌞 **Im Sonnenschutz halten**

Verhindert mehrfaches Hoch-/Runterfahren:

- Rollladen **bleibt im Sonnenschutz** auch wenn Bedingungen nicht mehr erfüllt
- Erst am Abend (Runterfahrzeit) wird neu evaluiert
- Besonders praktisch bei **Jalousien** (Lamellen bleiben geschlossen)

---

### 9. ☀️ **Helligkeits-Ende Verzögerung**

Verzögert das **Ende der Beschattung**:

- **Verzögerung (0-60 Minuten)**: Z.B. 10 Minuten
- Bei kurzer Bewölkung fährt Rollladen nicht sofort hoch
- Nur aktiv wenn **Helligkeitssensor** konfiguriert ist

---

### 10. ☀️ **Im Sommer nicht schließen**

Profile können im **Sommer ausgeschlossen** werden:

- **Global**: Sommerzeitraum definieren (z.B. 01.05. - 30.09.)
- **Pro Profil**: "Im Sommer nicht schließen" aktivieren
- Nützlich für:
  - Nord-Fenster (keine Beschattung nötig)
  - Räume die Wärme brauchen

---

## 🎨 Verbesserungen

### UI/UX
- ✅ **Entity-Selektoren** mit Auto-Vervollständigung
- ✅ **Zeit-Validierung** im ConfigFlow (HH:MM Format)
- ✅ **Vollständige Übersetzungen** (DE/EN)

### Global Settings
- ✅ **Sommerzeitraum** konfigurierbar
- ✅ **Sonnen-Offsets** (Hochfahren +/-X Minuten)
- ✅ **Sonnenhöhe-Ende** (Beschattung endet ab X°)

### Runtime
- ✅ **Race-Condition Fix** beim HA-Start
- ✅ **Runtime-Validation** von Cover-Entities
- ✅ **Rate-Limiting** für Warnungen

---

## 📦 Neue Entities

### Pro Profil:
- `sensor.shutterpilot_<profil>_status` - Status (Aktiv/Inaktiv/Cooldown)
- `sensor.shutterpilot_<profil>_last_action` - Letzte Aktion mit Grund
- `sensor.shutterpilot_<profil>_cooldown_remaining` - Verbleibender Cooldown (Sekunden)
- `sensor.shutterpilot_<profil>_sun_elevation` - Sonnenhöhe + Azimut
- `switch.shutterpilot_<profil>_automation` - Profil-Automatik ein/aus

---

## 🔧 Breaking Changes

**Keine!** Alle bestehenden Konfigurationen bleiben kompatibel.

**Neue Felder** haben sinnvolle Defaults:
- Hysterese: 0% (deaktiviert)
- Verzögerungen: 0 Sekunden
- Wärmeschutz: Deaktiviert
- Zwischenposition: Deaktiviert
- Im Sonnenschutz halten: Deaktiviert
- Sommer-Ausnahme: Deaktiviert

---

## 📊 Vergleich zu v0.2.7

| Feature | v0.2.7 | v0.3.0 |
|---------|--------|--------|
| Profile | ✅ | ✅ |
| Bereiche | ❌ | ✅ |
| Management Card | ❌ | ✅ |
| Golden Hour | ❌ | ✅ |
| Hysterese | ❌ | ✅ |
| Verzögerungen | ❌ | ✅ |
| Zwischenposition | ❌ | ✅ |
| Wärmeschutz | ❌ | ✅ |
| Sommer-Ausnahme | ❌ | ✅ |
| Entity-Selektoren | ❌ | ✅ |
| Profil-Switches | ✅ | ✅ |
| Status-Sensoren | ✅ | ✅ |

---

## 🚀 Migration von v0.2.7

1. **Backup erstellen**: Export der ShutterPilot-Konfiguration
2. **Update installieren**: Via HACS
3. **HA neu starten**
4. **Bereiche konfigurieren** (Optional):
   - Einstellungen → ShutterPilot → Konfigurieren
   - "Bereiche verwalten"
5. **Profile zuordnen** (Optional):
   - Profile bearbeiten
   - Bereich auswählen
6. **Management Card installieren** (Optional aber empfohlen)

---

## 🎯 Use Cases

### 1. **Familienwohnung mit 3 Bereichen**

**Wohnbereich** (Golden Hour):
- Woche: Hoch 06:30, Runter Golden Hour
- Wochenende: Hoch 08:00, Runter Golden Hour
- Profile: Wohnzimmer, Küche, Esszimmer

**Schlafbereich** (Nur Zeit):
- Woche: Hoch 06:00, Runter 22:30
- Wochenende: Hoch 09:00, Runter 23:30
- Profile: Schlafzimmer Eltern, Badezimmer

**Kinderbereich** (Sonnenstand):
- Woche: Hoch 06:45, Runter Sonnenuntergang
- Wochenende: Hoch 08:30, Runter Sonnenuntergang
- Profile: Kinderzimmer 1, Kinderzimmer 2

---

### 2. **Büro mit Hitzeschutz**

**Profil: Büro Südfenster**
- Bereich: Wohnbereich
- Lux-Sensor: sensor.brightness_outside
- Lux-Schwellwert: 30000 lx
- Lux-Hysterese: 20%
- Temperatur-Sensor: sensor.office_temperature
- Temp-Schwellwert: 24°C
- Temp-Hysterese: 10%
- **Wärmeschutz**: ✅ Aktiviert
- **Wärmeschutz-Temperatur**: 28°C
- **Im Sonnenschutz halten**: ✅ Aktiviert

**Verhalten:**
- Bei 30000 lx + 24°C: Beschattung auf 20%
- Bei 28°C: Vollständig geschlossen (0%)
- Bleibt geschlossen bis Runterfahrzeit am Abend

---

### 3. **Wohnzimmer mit Weihnachts-Schwibbögen**

**Profil: Wohnzimmer**
- Bereich: Wohnbereich
- Runterfahrzeit: 22:00
- **Zwischenposition**: 40%
- **Zwischenzeit**: 17:00

**Verhalten:**
- 17:00: Rollladen auf 40% (Schwibbögen sichtbar)
- 22:00: Rollladen auf 0% (vollständig geschlossen)

---

## 🐛 Bekannte Probleme

Keine! Alle bekannten Bugs aus v0.2.7 wurden behoben.

---

## 📝 Credits

- **Inspiriert von**: ioBroker shuttercontrol
- **Entwickelt für**: Home Assistant
- **Design**: Home Assistant Design Language
- **Made with ❤️**

---

## 💬 Feedback

Wir freuen uns über Feedback! 

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/fschube/shutterpilot/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/fschube/shutterpilot/discussions)
- ⭐ **Gefällt dir ShutterPilot?** Gib uns einen Stern auf GitHub!

---

**ShutterPilot v0.3.0 - Professional. Complete. Functional.**

