# Changelog v0.3.12

## 🎯 Hauptänderung: Dynamische Feldanzeige in Bereichskonfiguration

### Problembeschreibung
In Version 0.3.11 wurden alle Konfigurationsfelder für Bereiche unabhängig vom gewählten Steuerungsmodus angezeigt. Dies führte zu Unübersichtlichkeit und Verwirrung, da beispielsweise im Helligkeit-Modus auch Zeitfelder angezeigt wurden, die nicht relevant waren.

### Lösung: 2-Schritt-Konfigurationsprozess

Die Bereichsbearbeitung wurde in einen **2-Schritt-Prozess** umgewandelt:

#### Schritt 1: Name und Steuerungsart wählen
```
- Bereichsname
- Steuerungsart (Zeit/Sonne/Golden Hour/Helligkeit)
- [Optional] Löschen-Option für benutzerdefinierte Bereiche
```

#### Schritt 2: Modus-spezifische Felder
Je nach gewählter Steuerungsart werden nun **nur die relevanten Felder** angezeigt:

**🕐 Nur Zeit (TIME_ONLY)**
- Hochfahrzeit Wochentag
- Runterfahrzeit Wochentag
- Hochfahrzeit Wochenende
- Runterfahrzeit Wochenende
- Versatz zwischen Rollläden

**☀️ Sonnenstand (SUN) / Golden Hour**
- Alle Zeitfelder wie bei "Nur Zeit"
- **Zusätzlich:**
  - Früheste Hochfahrzeit
  - Späteste Hochfahrzeit
  - Versatz zwischen Rollläden

**💡 Helligkeit (BRIGHTNESS)**
- Helligkeitssensor auswählen
- Helligkeit zum Runterfahren (Lux)
- Helligkeit zum Hochfahren (Lux)
- Früheste Hochfahrzeit
- Späteste Hochfahrzeit
- Versatz zwischen Rollläden

### Technische Details

**Warum 2 Schritte?**
Home Assistant Config Flows laden das Schema nur einmal beim Öffnen des Formulars. Dynamisches Ein-/Ausblenden von Feldern während der Eingabe ist nicht möglich. Durch den 2-Schritt-Prozess wird beim Wechsel zwischen den Schritten das Schema neu geladen und zeigt nur die relevanten Felder an.

**Code-Änderungen:**
- `async_step_edit_area`: Schritt 1 - Name und Modus auswählen
- `async_step_edit_area_details`: Schritt 2 - Modus-spezifische Detail-Felder
- `self._temp_area_data`: Zwischenspeicher für Daten zwischen den Schritten

### Vorteile

✅ **Übersichtlichkeit**: Nur relevante Felder werden angezeigt  
✅ **Intuitive Bedienung**: Benutzer sehen direkt, welche Felder für ihren Modus wichtig sind  
✅ **Weniger Fehler**: Reduzierte Verwirrung bei der Konfiguration  
✅ **Saubere UX**: Jeder Modus hat seine eigene, angepasste Konfigurationsseite  

## 📋 Alle Änderungen

### Geändert
- **Config Flow**: 2-Schritt-Prozess für Bereichsbearbeitung implementiert
- **UI**: Dynamische Feldanzeige basierend auf gewähltem Steuerungsmodus

### Technisch
- Hinzugefügt: `self._temp_area_data` für temporäre Datenspeicherung zwischen Schritten
- Aufgeteilt: `async_step_edit_area` in zwei separate Schritte
- Neu: `async_step_edit_area_details` für modus-spezifische Konfiguration

## 🔄 Upgrade-Hinweise

Diese Version ist vollständig kompatibel mit v0.3.11. Es sind keine Migrationsschritte erforderlich. Die Bereichskonfiguration verwendet nun automatisch den neuen 2-Schritt-Prozess.

## 🐛 Bekannte Probleme

Keine bekannten Probleme in dieser Version.

---

**Version**: 0.3.12  
**Datum**: 20. November 2024  
**Kompatibilität**: Home Assistant Core 2024.1+

