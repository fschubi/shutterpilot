# ShutterPilot v0.3.12 - Dynamische UI-Verbesserung 🎨

## 🎯 Hauptfeature: Intelligente Feldanzeige

Diese Version verbessert die **Benutzerfreundlichkeit** der Bereichskonfiguration erheblich!

### Was ist neu?

Die Bereichsbearbeitung verwendet jetzt einen **2-Schritt-Prozess**, der nur die **relevanten Felder** für den gewählten Steuerungsmodus anzeigt:

#### 1️⃣ Schritt: Steuerungsart wählen
Wählen Sie Name und Steuerungsart für Ihren Bereich

#### 2️⃣ Schritt: Felder konfigurieren
Nur die für Ihre Steuerungsart relevanten Felder werden angezeigt:

- **🕐 Nur Zeit**: Hoch-/Runterfahrzeiten + Versatz
- **☀️ Sonnenstand/Golden Hour**: Zeitfenster + Earliest/Latest + Versatz
- **💡 Helligkeit**: Sensor + Lux-Werte + Earliest/Latest + Versatz

### Warum diese Änderung?

**Vorher**: Alle Felder wurden immer angezeigt, unabhängig vom Modus  
**Jetzt**: Nur relevante Felder für den gewählten Modus sind sichtbar

Das macht die Konfiguration **übersichtlicher** und **intuitiver**! 🎉

## 📦 Installation

### HACS (empfohlen)
1. Öffnen Sie HACS in Home Assistant
2. Gehen Sie zu "Integrationen"
3. Suchen Sie nach "ShutterPilot"
4. Klicken Sie auf "Aktualisieren auf v0.3.12"
5. Starten Sie Home Assistant neu

### Manuell
1. Laden Sie `shutterpilot.zip` herunter
2. Extrahieren Sie den Ordner nach `custom_components/shutterpilot/`
3. Starten Sie Home Assistant neu

## 🔄 Upgrade von v0.3.11

✅ **Nahtloses Upgrade** - keine Konfigurationsänderungen erforderlich!

Ihre bestehenden Bereiche und Profile bleiben vollständig erhalten. Die neue UI wird automatisch beim nächsten Bearbeiten eines Bereichs aktiv.

## 📸 Screenshots

### Vorher (v0.3.11)
Alle Felder waren immer sichtbar - unübersichtlich und verwirrend.

### Jetzt (v0.3.12)
**Nur relevante Felder** für den gewählten Modus werden angezeigt.

---

**Beispiel: Helligkeit-Modus**
```
✓ Helligkeitssensor
✓ Helligkeit zum Runterfahren (Lux)
✓ Helligkeit zum Hochfahren (Lux)
✓ Früheste Hochfahrzeit
✓ Späteste Hochfahrzeit
✓ Versatz zwischen Rollläden

✗ Hoch-/Runterfahrzeiten (nicht benötigt im Helligkeit-Modus)
```

## 🐛 Bugfixes

Keine Bugfixes in dieser Version - rein UI-Verbesserung!

## 📋 Vollständiges Changelog

Siehe [CHANGELOG_v0.3.12.md](CHANGELOG_v0.3.12.md) für alle technischen Details.

## 🙏 Feedback

Haben Sie Feedback oder Probleme mit dieser Version? 
- [Issue auf GitHub öffnen](https://github.com/fschube/shutterpilot/issues)
- [Diskussion starten](https://github.com/fschube/shutterpilot/discussions)

## ⭐ Gefällt Ihnen ShutterPilot?

Wenn Ihnen diese Integration gefällt, geben Sie dem Projekt einen Stern auf GitHub! ⭐

---

**Version**: 0.3.12  
**Release-Datum**: 20. November 2024  
**Kompatibilität**: Home Assistant 2024.1+

