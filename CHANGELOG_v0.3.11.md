# ShutterPilot v0.3.11 - UX Verbesserungen

## 🚀 Veröffentlichungsdatum: Januar 2025

---

## 🎨 UX-Verbesserungen

### **1. Dynamische Feld-Anzeige im Bereichs-Editor**

Die Konfiguration ist jetzt **viel übersichtlicher**! Je nach gewähltem Steuerungsart-Modus werden nur die **relevanten Felder** angezeigt.

#### **Modus: Nur Zeit**
```
✅ Angezeigt:
- Hochfahrzeit Wochentag/Wochenende
- Runterfahrzeit Wochentag/Wochenende
- Verzögerung zwischen Rollläden

🚫 Versteckt:
- Früheste/Späteste Hochfahrzeit (nicht benötigt)
- Helligkeitssensor
- Lux-Werte
```

#### **Modus: Sonnenstand / Golden Hour**
```
✅ Angezeigt:
- Hochfahrzeit Wochentag/Wochenende
- Runterfahrzeit Wochentag/Wochenende
- Früheste/Späteste Hochfahrzeit ⭐
- Verzögerung zwischen Rollläden

🚫 Versteckt:
- Helligkeitssensor
- Lux-Werte
```

#### **Modus: Helligkeit (Lux-basiert)**
```
✅ Angezeigt:
- Helligkeitssensor ⭐
- Lux runterfahren ⭐
- Lux hochfahren ⭐
- Früheste/Späteste Hochfahrzeit (als Sicherheit)
- Verzögerung zwischen Rollläden

🚫 Versteckt:
- Hochfahrzeit Wochentag/Wochenende
- Runterfahrzeit Wochentag/Wochenende
```

**Vorteile:**
- ✅ **Übersichtlicher** - Keine irrelevanten Felder
- ✅ **Weniger Verwirrung** - Nur das Nötige wird angezeigt
- ✅ **Intelligenter** - Alte Werte bleiben beim Modus-Wechsel erhalten
- ✅ **Flexibler** - Einfacher Wechsel zwischen Modi

---

## 🆕 Benutzerdefinierte Bereiche

### **Unbegrenzt viele eigene Bereiche erstellen!**

Zusätzlich zu den 3 Standard-Bereichen (Wohn/Schlaf/Kinder) können jetzt **eigene Bereiche** angelegt werden:

**Beispiele:**
- 🏢 **Büro** (Helligkeits-basiert, 09:00-17:00)
- 🚪 **Gästezimmer** (Nur Zeit, flexibel)
- 🏠 **Eingangsbereich** (Sonnenstand)
- 🛏️ **Elternschlafzimmer** (Eigene Zeiten)
- 👶 **Babyzimmer** (Spezielle Zeiten)

**Features:**
- ✅ **Erstellen**: Eigene Bereiche mit individuellem Namen und ID
- ✅ **Bearbeiten**: Alle Einstellungen anpassbar
- ✅ **Löschen**: Nur wenn keine Profile zugeordnet
- ✅ **Automatische Integration**: Erscheinen sofort in Profil-Zuweisung
- ✅ **Validierung**: Prüft auf doppelte IDs und verhindet Löschung mit zugewiesenen Profilen

---

## 🔧 Technische Änderungen

### **const.py:**
```python
DEFAULT_AREAS = [AREA_LIVING, AREA_SLEEPING, AREA_CHILDREN]
```

### **config_flow.py:**

**Neue Funktionen:**
- `async_step_add_area()` - Neuen Bereich erstellen
- Dynamisches Schema in `async_step_edit_area()` basierend auf Modus
- Lösch-Option für benutzerdefinierte Bereiche (nicht für Standard-Bereiche)
- Intelligentes Speichern - Nicht angezeigte Felder werden mit Defaults beibehalten
- Dynamische Bereichs-Auswahl in Profil-Konfiguration

**Bereichs-Verwaltung:**
```
Bereiche verwalten:
├── Zurück zum Hauptmenü
├── ➕ Neuen Bereich hinzufügen
├── ✏️ Wohnbereich (Standard)
├── ✏️ Schlafbereich (Standard)
├── ✏️ Kinderbereich (Standard)
├── ✏️ Büro (Bearbeiten/Löschen) ⭐ NEU
└── ✏️ Gästezimmer (Bearbeiten/Löschen) ⭐ NEU
```

---

## 📊 Workflow: Eigenen Bereich erstellen

### **1. Bereich hinzufügen**
```
Einstellungen → ShutterPilot → Konfigurieren
→ "Bereiche verwalten"
→ "➕ Neuen Bereich hinzufügen"

Eingabe:
- Bereichs-ID: buero (nur Buchstaben, Zahlen, _)
- Bereichsname: Büro
- Steuerungsart: Helligkeit (Lux-basiert)
```

### **2. Bereich konfigurieren**
```
→ Automatische Weiterleitung zum Editor
→ NUR relevante Felder werden angezeigt:
  - Helligkeitssensor: sensor.office_brightness
  - Lux runterfahren: 3000 lx
  - Lux hochfahren: 10000 lx
  - Früheste Hochfahrzeit: 08:00
  - Späteste Hochfahrzeit: 18:00
  - Verzögerung: 5 Sekunden
```

### **3. Profile zuordnen**
```
→ Profil erstellen/bearbeiten
→ "Bereich zuordnen"
→ Dropdown zeigt jetzt auch "Büro" ✅
```

---

## 🗑️ Bereich löschen

**Sicherheits-Features:**
- ⚠️ **Standard-Bereiche** können NICHT gelöscht werden
- ⚠️ **Bereiche mit zugewiesenen Profilen** können NICHT gelöscht werden
- ✅ **Fehlermeldung** mit Anzahl zugewiesener Profile

**Workflow:**
```
1. Bereich bearbeiten
2. Checkbox "⚠️ Diesen Bereich löschen" aktivieren
3. Speichern
   → Erfolg: Bereich gelöscht
   → Fehler: "Kann nicht gelöscht werden: 3 Profile sind diesem Bereich zugeordnet"
```

---

## 🌍 Übersetzungen

**Deutsch:**
- "Neuen Bereich hinzufügen"
- "Bereichs-ID"
- "⚠️ Diesen Bereich löschen"
- Dynamische Beschreibungen

**Englisch:**
- "Add New Area"
- "Area ID"
- "⚠️ Delete this area"
- Dynamic descriptions

---

## 📝 Breaking Changes

**Keine!** Alle bestehenden Konfigurationen bleiben vollständig kompatibel.

**Standard-Bereiche:**
- Bleiben wie bisher: Wohn, Schlaf, Kinder
- Können nicht gelöscht werden
- Profile können weiterhin zugeordnet werden

---

## 🚀 Migration von v0.3.10

1. **Update installieren** via HACS
2. **Home Assistant neu starten**
3. **Keine weiteren Schritte nötig!**

**Optional - Eigene Bereiche erstellen:**
```
Einstellungen → ShutterPilot → Konfigurieren
→ Bereiche verwalten
→ ➕ Neuen Bereich hinzufügen
```

---

## 💡 Use Cases

### **Beispiel 1: Büro mit Helligkeitssteuerung**
```
Bereich: Büro
Modus: Helligkeit
Sensor: sensor.office_brightness
Lux runter: 3000
Lux hoch: 10000
Früheste: 08:00 (nicht vor Arbeitsbeginn)
Späteste: 18:00 (spätestens nach Feierabend)

Profil: Büro-Rollladen
Zuordnung: Büro
→ Automatisch gesteuert per Helligkeit
```

### **Beispiel 2: Gästezimmer mit festen Zeiten**
```
Bereich: Gästezimmer
Modus: Nur Zeit
Hoch Woche: 09:00
Runter Woche: 22:00
Hoch Wochenende: 10:00
Runter Wochenende: 23:00

Profil: Gästezimmer-Rollladen
Zuordnung: Gästezimmer
→ Einfache Zeitsteuerung, unabhängig von Sonne
```

### **Beispiel 3: Elternschlafzimmer mit Golden Hour**
```
Bereich: Elternschlafzimmer
Modus: Golden Hour
Hoch Woche: 06:30
Runter Woche: Golden Hour
Früheste: 06:00
Späteste: 07:30

Profil: Eltern-Rollladen
Zuordnung: Elternschlafzimmer
→ Sanfte Golden Hour Steuerung
```

---

## 📖 Dokumentation

**Siehe auch:**
- [README.md](README.md) - Vollständige Dokumentation
- [CHANGELOG_v0.3.10.md](CHANGELOG_v0.3.10.md) - Vorherige Version
- [GitHub Issues](https://github.com/fschube/shutterpilot/issues) - Bug Reports

---

## 🙏 Credits

- **Feature-Request**: User-Feedback für bessere UX
- **Inspiration**: Professionelle Konfigurations-UIs
- **Made with ❤️ for Home Assistant**

---

**ShutterPilot v0.3.11 - Flexibel. Übersichtlich. Individuell.**

