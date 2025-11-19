# ShutterPilot v0.3.10 - Changelog

## 🚀 Veröffentlichungsdatum: Januar 2025

---

## 🎯 Hauptfeatures

### ☀️ **Neue Steuerungsart: Helligkeit (Lux-basiert)**

Bereiche können jetzt direkt über Helligkeitssensoren gesteuert werden - unabhängig von Sonnenstand und Zeit!

**Neue Bereichs-Konfiguration:**
- **Modus**: "Helligkeit (Lux-basiert)"
- **Helligkeitssensor**: Wähle einen Lux-Sensor für den Bereich
- **Lux runterfahren**: Schwellwert für Schließen (z.B. 5000 lx)
- **Lux hochfahren**: Schwellwert für Öffnen (z.B. 15000 lx)

**Vorteile:**
- ✅ Reagiert auf tatsächliche Helligkeit (Bewölkung, Jahreszeit)
- ✅ Unabhängig von Sonnenauf-/-untergang
- ✅ Automatische Hysterese (5000-15000 lx = keine Aktion)

---

## 🔧 Intelligente Trigger-Logik

### **Trigger-basiertes System** (wie ioBroker shuttercontrol)

**Ersetzt das Cooldown-System durch intelligente Trigger:**

1. **System fährt hoch** → `triggered_up = TRUE`
2. **Manuelle Änderung** → Position wird **UNBEGRENZT** respektiert
3. **Erst nächster Trigger** (runter ODER hoch) greift wieder ein
4. **Tägliches Reset** um 3 Uhr → Alle Flags zurückgesetzt

**Beispiel:**
```
09:00  → System fährt hoch (100%)
11:00  → Du fährst manuell auf 50% (TV-Blendung)
12:00  → System respektiert 50% bis:
         - Helligkeit fällt unter 5000 lx ODER
         - Tägliches Reset um 3 Uhr
```

---

## 🪟 Intelligente Fenster/Tür-Logik

### **`window_not_close` Flag** (wie in Original-Automationen)

**Fenster-Reaktion nur wenn Rollladen unten:**

| Situation | Fenster öffnen | Verhalten |
|-----------|----------------|-----------|
| **Rollladen OBEN** | 🪟 Öffnet | 🚫 **Ignoriert** (bleibt oben) |
| **Rollladen UNTEN** | 🪟 Öffnet | ⬆️ **Lüftungsposition** (20%) |

**Vorteile:**
- ✅ Macht keinen Sinn, von 100% auf 20% zu fahren
- ✅ Fenster-Lüftung nur wenn Rollladen unten
- ✅ Spart unnötige Bewegungen

---

## 🚪 Tür-Sensor mit 3 Zuständen

**Unterstützt jetzt 3-Zustands-Sensoren:**

1. **`closed`** = Zu → Normale Automatik
2. **`tilted`** = Gekippt → Lüftungsposition (wie Fenster)
3. **`open`** = Offen → **Aussperrschutz** (IMMER, unabhängig von Position)

**Aussperrschutz:**
- Tür `open` → Fährt **IMMER** auf `door_safe_position` (z.B. 80%)
- Unabhängig von `window_not_close` Flag
- Verhindert Aussperren bei offener Tür

---

## 📊 Vollständiges Beispiel-Szenario

```
06:00  → Lux: 2000   → Kein Trigger (zu dunkel)
09:00  → Lux: 18000  → ☀️ HOCH (100%)         [triggered_up=TRUE, window_not_close=FALSE]
10:00  → 🪟 Fenster → 🚫 IGNORIERT            [Rollladen bleibt bei 100%]
11:00  → 👤 Manual  → 50% respektiert         [Position bleibt bis nächster Trigger]
14:00  → 🪟 Fenster → 🚫 IGNORIERT            [window_not_close=FALSE]
18:00  → Lux: 4000  → 🌙 RUNTER               [triggered_down=TRUE, window_not_close=TRUE]
       → 🪟 Fenster offen → Nur 20%! ✅
18:05  → 🪟 schließt → Cooldown 120s
       → Nach Cooldown → Ganz runter (0%) ✅
19:00  → 🪟 öffnet  → Auf 20% (Lüftung) ✅    [window_not_close=TRUE]
03:00  → 🌅 Reset   → Alle Flags zurück
```

---

## 🆕 Neue Konstanten

**`const.py`:**
```python
MODE_BRIGHTNESS = "brightness"
A_BRIGHTNESS_SENSOR = "brightness_sensor"
A_BRIGHTNESS_DOWN = "brightness_down_lux"
A_BRIGHTNESS_UP = "brightness_up_lux"
```

---

## 🔧 Technische Änderungen

### **coordinator.py:**
- ✅ Trigger-Flags: `_triggered_up`, `_triggered_down`
- ✅ `_window_not_close` Flag für intelligente Fenster-Logik
- ✅ Tägliches Reset um 3 Uhr via `async_track_time_change`
- ✅ Helligkeits-basierte Steuerung in `evaluate_policy_and_apply()`
- ✅ Tür-Sensor mit 3 Zuständen (`closed`/`tilted`/`open`)
- ✅ Manuelle Änderungs-Erkennung (ohne Cooldown-Aktivierung)

### **config_flow.py:**
- ✅ Bereichs-Editor mit Helligkeitsfeldern
- ✅ Entity-Selektor für Helligkeitssensor
- ✅ Default-Werte: 5000 lx (runter), 15000 lx (hoch)

### **Übersetzungen:**
- ✅ Deutsch: "Helligkeit (Lux-basiert)"
- ✅ Englisch: "Brightness (Lux-based)"
- ✅ Beschreibungen für alle neuen Felder

---

## 🐛 Behobene Probleme

- ❌ **ALT**: Cooldown von 120s zu kurz für manuelle Änderungen
- ✅ **NEU**: Trigger-System respektiert Position unbegrenzt

- ❌ **ALT**: Fenster öffnen bei hochgefahrenem Rollladen → Fährt auf 20%
- ✅ **NEU**: Fenster wird ignoriert wenn Rollladen oben

- ❌ **ALT**: Tür-Sensor nur 2 Zustände (on/off)
- ✅ **NEU**: 3 Zustände (closed/tilted/open)

- ❌ **ALT**: Kein tägliches Reset
- ✅ **NEU**: Reset um 3 Uhr (alle Trigger zurückgesetzt)

---

## 📝 Breaking Changes

**Keine!** Alle bestehenden Konfigurationen bleiben kompatibel.

**Neue Features sind optional:**
- Helligkeits-Modus muss explizit gewählt werden
- Trigger-System greift automatisch
- `window_not_close` Logik ist immer aktiv (verbessert Verhalten)

---

## 🚀 Migration von v0.3.9

1. **Update installieren** via HACS
2. **Home Assistant neu starten**
3. **Optional**: Bereiche auf "Helligkeit" umstellen
   - Einstellungen → ShutterPilot → Konfigurieren
   - Bereiche verwalten → Bereich bearbeiten
   - Modus: "Helligkeit (Lux-basiert)"
   - Helligkeitssensor auswählen
   - Lux-Werte konfigurieren

---

## 📖 Dokumentation

**Siehe auch:**
- [README.md](README.md) - Vollständige Dokumentation
- [GitHub Issues](https://github.com/fschube/shutterpilot/issues) - Bug Reports
- [GitHub Discussions](https://github.com/fschube/shutterpilot/discussions) - Feature Requests

---

## 💡 Inspiration

Diese Version wurde inspiriert von User-Feedback und Original-Automationen für helligkeitsbasierte Rollladensteuerung. Das Trigger-System basiert auf bewährten Konzepten aus ioBroker's shuttercontrol.

---

## 🙏 Credits

- **Entwickelt für**: Home Assistant Community
- **Inspiriert von**: ioBroker shuttercontrol, User-Automationen
- **Made with ❤️**

---

**ShutterPilot v0.3.10 - Intelligent. Respektvoll. Zuverlässig.**

