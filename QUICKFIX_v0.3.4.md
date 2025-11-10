# 🚀 QuickFix v0.3.4 - Config-Sensor Problem

## ⚠️ Problem
- Card zeigt "Keine Profile vorhanden"
- Console-Fehler: "ShutterPilot Config Sensor nicht gefunden"
- Profile aus Integration werden nicht in Card angezeigt
- Speichern funktioniert nicht

## ✅ Lösung
Die Config wird jetzt über einen **dedizierten Sensor** bereitgestellt:
- **Sensor Entity-ID**: `sensor.shutterpilot_config`
- **Automatisch aktiviert** (nicht mehr versteckt)
- **Aktualisiert sich automatisch** bei Config-Änderungen

---

## 📦 Installation

### 1. Integration aktualisieren

**Option A: Manuell kopieren**
```powershell
# Kopiere aktualisierte Dateien
xcopy "C:\dev\shutterpilot\custom_components\shutterpilot\*" "\\wsl$\homeassistant\config\custom_components\shutterpilot\" /E /Y
```

**Option B: Via HACS (wenn vorhanden)**
```
HACS → Integrationen → ShutterPilot → Neu installieren
```

### 2. Card aktualisieren
```powershell
copy "C:\dev\shutterpilot\www\shutterpilot-card.js" "\\wsl$\homeassistant\config\www\shutterpilot-card.js" -Force
```

### 3. Home Assistant neu starten
```
Einstellungen → System → Neu starten
```

**WICHTIG**: Ein einfaches "Integration neu laden" reicht NICHT aus!
Der Config-Sensor wird nur beim HA-Start korrekt erstellt.

### 4. Browser-Cache leeren
```
Strg + Shift + R (mehrmals!)
```

---

## 🔍 Verifikation

### Schritt 1: Prüfe ob Config-Sensor existiert

**Entwicklertools → States**
```
Suche: "shutterpilot_config"

✅ Sollte gefunden werden: sensor.shutterpilot_config
   State: OK
   Attributes:
     entry_id: "abc123..."
     profiles: [...]
     areas: {...}
     global_settings: {...}
```

**Falls nicht gefunden:**
```powershell
# Prüfe ob Sensor erstellt wurde
# In HA: Entwicklertools → Template
{{ states('sensor.shutterpilot_config') }}

# Sollte "OK" zurückgeben
```

### Schritt 2: Prüfe Card Console

**Browser F12 → Console**
```
Erwartete Logs beim Laden der Card:

✅ SHUTTERPILOT-CARD Version 2.1.0
✅ Config Sensor geladen: {entry_id: "...", profiles: [...], ...}
✅ 3 Profile geladen: ["Wohnzimmer", "Schlafzimmer", "Küche"]
```

**Falls Fehler:**
```
❌ ShutterPilot Config Sensor nicht gefunden: sensor.shutterpilot_config
   Verfügbare Sensoren: [...]

→ HA komplett neu starten!
→ Integration löschen und neu hinzufügen
```

### Schritt 3: Teste Speichern

**1. Neues Profil erstellen**
```
Card → "+ Neues Profil"
Name: TestProfil123
Cover: cover.test
→ Speichern
```

**2. Console prüfen**
```
Erwartete Logs:

💾 Speichere Config: {profiles: 4, areas: 3}
✅ Service-Call erfolgreich
✅ Konfiguration gespeichert
```

**3. Backend-Log prüfen**
```
Einstellungen → System → Logs

Erwartete Logs:

INFO (MainThread) [custom_components.shutterpilot] update_config service called with 4 profiles and 3 areas
INFO (MainThread) [custom_components.shutterpilot] Config entry updated, will reload automatically
INFO (MainThread) [custom_components.shutterpilot] Config entry updated, reloading ShutterPilot integration
INFO (MainThread) [custom_components.shutterpilot] ShutterPilot setup complete with 4 profile(s).
```

**4. Verifiziere Persistenz**
```
HA komplett neu starten
→ Card öffnen
→ Profil "TestProfil123" sollte noch da sein
```

---

## 🐛 Debugging

### Problem: "Config Sensor nicht gefunden"

**Mögliche Ursachen:**

1. **Sensor wurde nicht erstellt**
   ```
   Lösung: HA komplett neu starten (nicht nur reload!)
   ```

2. **Sensor ist deaktiviert**
   ```
   Einstellungen → Geräte → ShutterPilot
   → Entities → "ShutterPilot Config" → Aktivieren
   ```

3. **Sensor hat falsche Entity-ID**
   ```
   Entwicklertools → States
   → Suche: "shutterpilot"
   → Prüfe welche Sensoren existieren
   
   Falls anders benannt:
   → Integration löschen
   → custom_components/shutterpilot/ löschen
   → Neu installieren
   → HA neu starten
   ```

### Problem: Profile werden nicht angezeigt

**Check 1: Sind Profile in der Integration konfiguriert?**
```
Einstellungen → Geräte & Dienste → ShutterPilot
→ ⋮ → Optionen
→ Profile anzeigen
```

**Check 2: Sind Profile im Config-Sensor?**
```
Entwicklertools → States → sensor.shutterpilot_config
→ Attributes → profiles

Falls leer: []
→ Profile sind nicht in der Config!
→ In Integration über ConfigFlow hinzufügen
```

**Check 3: Lädt die Card die Profile?**
```
F12 → Console

Erwartetes Log:
✅ 3 Profile geladen: ["Wohnzimmer", ...]

Falls:
✅ 0 Profile geladen: []
→ Config-Sensor hat keine Profile
→ In Integration konfigurieren
```

### Problem: Speichern funktioniert nicht

**Check 1: Service existiert?**
```
Entwicklertools → Services
→ Suche: "shutterpilot.update_config"

Falls nicht gefunden:
→ Integration nicht korrekt geladen
→ Logs prüfen auf Fehler beim Setup
```

**Check 2: Service-Call erfolgreich?**
```
F12 → Console

Erwartetes Log:
💾 Speichere Config: {profiles: 4, areas: 3}
✅ Service-Call erfolgreich

Falls Fehler:
→ Network Tab (F12) prüfen
→ WebSocket-Fehler?
→ Service nicht registriert?
```

**Check 3: Config wird aktualisiert?**
```
Backend-Logs (Settings → System → Logs)

Erwartetes Log:
INFO [custom_components.shutterpilot] update_config service called...
INFO [custom_components.shutterpilot] Config entry updated...

Falls nicht:
→ Service wird nicht aufgerufen
→ Card-Bug?
→ Console-Fehler prüfen
```

---

## 📋 Änderungen in v0.3.4

### Backend (`sensor.py`)
- ✅ Config-Sensor mit fester Entity-ID: `sensor.shutterpilot_config`
- ✅ Sensor ist standardmäßig **aktiviert** (nicht mehr versteckt)
- ✅ Kein `device_info` mehr (verhindert zusätzliche Prefixes)
- ✅ Update-Listener korrekt implementiert mit `@callback`
- ✅ Entry-Referenz wird bei Config-Änderungen aktualisiert

### Backend (`__init__.py`)
- ✅ Ausführliche Logs beim `update_config` Service
- ✅ Zeigt Anzahl der Profile und Areas
- ✅ Debug-Logs für Profilnamen und Area-Keys

### Card (`shutterpilot-card.js` v2.1.0)
- ✅ Sucht explizit nach `sensor.shutterpilot_config`
- ✅ Ausführliche Debug-Logs beim Laden
- ✅ Zeigt alle verfügbaren ShutterPilot-Sensoren falls Config-Sensor fehlt
- ✅ Debug-Logs beim Speichern
- ✅ Bessere Fehlermeldungen

---

## 🎯 Erwartetes Verhalten

### Beim HA-Start:
1. ShutterPilot Integration lädt
2. Config-Sensor wird erstellt: `sensor.shutterpilot_config`
3. Sensor ist **sofort verfügbar** (nicht deaktiviert)
4. Sensor enthält alle Profile, Areas und global_settings in Attributes

### Card lädt:
1. Card sucht nach `sensor.shutterpilot_config`
2. Liest `attributes.profiles`, `attributes.areas`, `attributes.global_settings`
3. Zeigt Profile in Tabelle an
4. Console-Log: "✅ X Profile geladen: [...]"

### Beim Speichern:
1. User klickt "Speichern"
2. Card ruft `shutterpilot.update_config` Service auf
3. Service aktualisiert Config Entry
4. Integration lädt automatisch neu
5. Config-Sensor aktualisiert sich
6. Card lädt Config neu (nach 1 Sekunde)
7. Änderungen sind sichtbar

---

## 🆘 Hilfe

Falls nach allen Schritten immer noch Probleme bestehen:

1. **Erstelle Debug-Report:**
   ```
   F12 → Console → Rechtsklick → "Save as..." → console.log
   Settings → System → Logs → Download full log
   ```

2. **Prüfe Entity Registry:**
   ```powershell
   # In Home Assistant Container:
   cat /config/.storage/core.entity_registry | grep shutterpilot
   
   # Sollte Config-Sensor zeigen:
   "entity_id": "sensor.shutterpilot_config"
   ```

3. **Nuclear Option:**
   ```
   1. Einstellungen → Geräte & Dienste → ShutterPilot → Löschen
   2. Lösche: /config/custom_components/shutterpilot/
   3. Lösche: /config/www/shutterpilot-card.js
   4. HA neu starten
   5. Neu installieren
   6. HA neu starten
   7. Card konfigurieren
   8. Browser-Cache leeren (Strg+Shift+R)
   ```

---

## ✨ Version Info

```
Backend: v0.3.4
- Config-Sensor mit fester Entity-ID
- Standardmäßig aktiviert
- Bessere Logs

Card: v2.1.0
- Explizite Sensor-Suche
- Ausführliche Debug-Logs
- Bessere Fehlermeldungen
```

**Datum**: 10.11.2025
**Fix für**: Config-Sensor nicht gefunden, Profile nicht sichtbar, Speichern funktioniert nicht

