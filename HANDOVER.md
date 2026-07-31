# E10 — Deployment-Handover für Yizzl

> **Version:** 1.0.0 | **Datum:** Juli 2026 | **Status:** Bereit zum Testen

---

## Server-Übersicht

| | PROD | TEST |
|---|---|---|
| **Domain** | `e10.projectmellon.de` | `test.e10.projectmellon.de` |
| **Port** | 25585 | 25580 |
| **RAM** | 12 GB | 6 GB |
| **Spieler** | 5–8 gleichzeitig | 1–2 (Mod-Tests) |
| **Modpack** | Enigmatica 10 v1.30.0 | Gleiches Modpack |
| **Minecraft** | 1.21.1 (NeoForge) | 1.21.1 (NeoForge) |

---

## Wie Yizzl connected

```
Server-Adresse:  e10.projectmellon.de
                 (SRV-Record leitet automatisch auf den richtigen Port)
```

TEST-Instanz:
```
Server-Adresse:  test.e10.projectmellon.de
```

---

## Dashboard (Web-UI)

```
https://e10.projectmellon.de
```

Das Dashboard hat zwei Tabs: **PROD** und **TEST**. Yizzl kann dort:

| Funktion | Beschreibung |
|---|---|
| 👥 **Spielerliste** | Zeigt alle online Spieler, updated alle 10 Sekunden |
| 📋 **Whitelist** | Spieler hinzufügen/entfernen (pro Instanz) |
| 📢 **MOTD** | 2-zeilige Server-Nachricht ändern (pro Instanz) |
| 💾 **Backups** | Manuelles Backup auslösen, Snapshots anzeigen & wiederherstellen |
| ⚙️ **RCON** | Direkte Server-Befehle senden |

### MOTD aktuell

Die MOTD sieht im Client so aus:
```
     Enigmatica 10          (cyan, bold)
  e10.projectmellon.de     (grau)
```

Kann Yizzl jederzeit selbst im Dashboard ändern.

---

## Backup & Rollback

Backups laufen automatisch alle **30 Minuten** (inkrementell via Borg).
Im Dashboard kann Yizzl jederzeit:

1. **Backup manuell triggern** → Button „Create Backup Now"
2. **Letzte Snapshots sehen** → Button „List Snapshots"
3. **Zurücksetzen** → Snapshot auswählen, „Restore“ klicken

Rollback stoppt den Server, stellt die Welt wieder her, und muss dann manuell gestartet werden.

---

## Grafana Dashboard

```
https://grafana.e10.projectmellon.de
User: admin
Passwort: (wird separat übergeben)
```

Zeigt: TPS, MSPT, Spielerzahl, RAM-Nutzung.

---

## E2E Tests

Nach jedem Deployment führen wir diese Tests aus:

```bash
cd ~/dev/e10
pip install mcstatus requests
python tests/e2e.py
```

Prüft: Server-Erreichbarkeit, MOTD-Format, Spielerliste, Web-UI, Grafana, DNS, Journald-Logs.

MOTD-Vorschau:
```bash
python tests/motd_viewer.py           # PROD
python tests/motd_viewer.py --port 25580  # TEST
```

---

## Yizzl's Checkliste ✅

- [ ] **Connect**: `e10.projectmellon.de` im Minecraft Client hinzugefügt
- [ ] **MOTD**: Sieht sauber aus (2 Zeilen, Farben korrekt)
- [ ] **Join**: Kann dem Server beitreten
- [ ] **Whitelist**: Dashboard öffnen → Spieler hinzufügen → funktioniert
- [ ] **TEST**: `test.e10.projectmellon.de` connecten → läuft separat
- [ ] **Backup**: Dashboard → „Create Backup Now" → „List Snapshots" → Snapshot sichtbar
- [ ] **Grafana**: `grafana.e10.projectmellon.de` öffnen → Login klappt, TPS sichtbar
- [ ] **Performance**: 20 TPS, kein Lag

---

## Momo's Checkliste (Intern)

- [ ] Homestead/Homestead2 pausiert → RAM frei
- [ ] Ansible Deploy lief durch ohne Fehler
- [ ] DNS SRV Records gesetzt (Cloudflare)
- [ ] Caddy auf projectmellon.de neu geladen
- [ ] `journalctl -t e10-prod -t e10-test -t e10-shared -f` → Logs fließen
- [ ] E2E Tests alle grün
- [ ] Borg Backup Cronjob eingerichtet
- [ ] Grafana Dashboard importiert (wenn vorhanden)
