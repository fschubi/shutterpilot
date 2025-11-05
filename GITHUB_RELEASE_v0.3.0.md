# 🚀 ShutterPilot v0.3.0 - Enterprise Release

## Was ist neu?

Diese Version bringt ShutterPilot auf **Enterprise-Level** - inspiriert von ioBroker's shuttercontrol! 🎯

### ⭐ Top Features

#### 🏠 **Bereichs-Management**
Definiere 3 globale Bereiche (Wohn/Schlaf/Kinder) mit eigenen Zeit-Templates:
- **3 Steuerungsarten**: Nur Zeit / Sonnenstand / **Golden Hour (NEU!)**
- **Wochentag/Wochenende**: Separate Zeiten
- **Stagger-Delay**: Zeitversatz zwischen Rollläden
- Profile automatisch zuordnen

#### 📊 **Professional Management Card**
Brandneue Custom Lovelace Card:
- ✅ Tabellarische Übersicht aller Profile
- ✅ Live Status-Anzeige (Aktiv/Inaktiv/Cooldown)
- ✅ Schnellaktionen: Bearbeiten, Kopieren, Löschen
- ✅ Bulk-Aktionen: Alle hoch/runter/stopp
- ✅ 3 Tabs: Profile / Bereiche / Global
- ✅ Modern & Responsive Design

![Management Card Preview](docs/images/card-preview.png)

#### 🌅 **Golden Hour**
- Rollläden fahren zur "Golden Hour"
- Ca. 1 Stunde vor Sonnenuntergang / nach Sonnenaufgang
- Pro Bereich konfigurierbar

#### 📈 **Erweiterte Automatisierung**
- **Sensor-Hysterese** (Lux/Temp) - verhindert Flackern
- **Fenster-Verzögerungen** - Delays beim Öffnen/Schließen
- **Zwischenposition** - Z.B. für Weihnachtsbeleuchtung
- **Wärmeschutz** - Vollständig schließen bei Hitze
- **Im Sonnenschutz halten** - Bis zum Abend
- **Sommer-Ausnahme** - Nicht schließen im Sommer
- **Helligkeits-Ende Verzögerung** - Verzögert Hochfahren

---

## 📦 Installation

### Via HACS (Empfohlen)

1. HACS → Custom Repositories → `https://github.com/fschube/shutterpilot`
2. HACS → Integrations → ShutterPilot installieren
3. Home Assistant neu starten
4. Integration hinzufügen: Einstellungen → Geräte & Dienste

### Management Card installieren

```yaml
# 1. Ressource hinzufügen (Einstellungen → Dashboards → Ressourcen)
URL: /local/community/shutterpilot/shutterpilot-card.js
Typ: JavaScript-Modul

# 2. Dashboard → Karte hinzufügen
type: custom:shutterpilot-card
entity: switch.shutterpilot_global_automation
```

---

## 🎯 Beispiel: Familienwohnung

### Bereiche konfigurieren

**Wohnbereich** (Golden Hour):
```
Woche: Hoch 06:30, Runter Golden Hour
Wochenende: Hoch 08:00, Runter Golden Hour
Verzögerung: 10s
```

**Schlafbereich** (Nur Zeit):
```
Woche: Hoch 06:00, Runter 22:30
Wochenende: Hoch 09:00, Runter 23:30
Verzögerung: 5s
```

**Kinderbereich** (Sonnenstand):
```
Woche: Hoch 06:45, Runter Sonnenuntergang
Wochenende: Hoch 08:30, Runter Sonnenuntergang
Verzögerung: 8s
```

### Profil: Büro mit Hitzeschutz

```
Bereich: Wohnbereich
Lux-Schwellwert: 30000 lx
Lux-Hysterese: 20%
Temp-Schwellwert: 24°C
Wärmeschutz: 28°C (vollständig schließen)
Im Sonnenschutz halten: ✅
```

---

## 📊 Feature-Vergleich

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

---

## 🐛 Bugfixes

- ✅ Race-Condition beim HA-Start behoben
- ✅ Lambda-Fehler in Switch-Listeners behoben
- ✅ Entity-Validation zur Laufzeit
- ✅ Rate-Limiting für Warnungen

---

## ⚠️ Breaking Changes

**Keine!** Alle bestehenden Konfigurationen bleiben kompatibel.

Neue Features haben sinnvolle Defaults (meist deaktiviert).

---

## 📚 Dokumentation

Vollständige Dokumentation: [README.md](README.md)
Detailliertes Changelog: [CHANGELOG_v0.3.0.md](CHANGELOG_v0.3.0.md)

---

## 🤝 Feedback & Support

- 🐛 Bug Reports: [GitHub Issues](https://github.com/fschube/shutterpilot/issues)
- 💡 Feature Requests: [GitHub Discussions](https://github.com/fschube/shutterpilot/discussions)
- ⭐ Gefällt dir ShutterPilot? **Gib uns einen Stern!**

---

**Made with ❤️ for Home Assistant**

