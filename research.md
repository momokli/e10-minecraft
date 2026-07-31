Projektplan: Modded Minecraft Server (Enigmatica 10)1. Projektübersicht & AnforderungenModpack: Enigmatica 10 (E10)Spieleranzahl: 5–8 Spieler (Gleichzeitig)Ressourcen: ~12 GB RAM, dedizierte Intel CPUTech Stack: Docker (itzg/minecraft-server), Caddy (Reverse Proxy), Web-UI (Custom / Management)2. Recherche-Auftrag (Komponenten)2.1 Enigmatica 10 (E10) & Docker (itzg/minecraft-server)Modloader & Version: Prüfung, ob NeoForge oder Forge erforderlich ist und welche Java-Version (meist Java 21 für neuere Packs) benötigt wird.Docker-Konfiguration: Optimale Umgebungsvariablen für itzg/minecraft-server (z. B. TYPE=NEOFORGE, VERSION=<version>, INIT_MEMORY=4G, MAX_MEMORY=12G, EULA=TRUE).Performance-Flags: JVM-Argumente für Garbage Collection (Aikar's Flags angepasst an Java 21).2.2 Waiting Cage (Start-Restriktion)Mechanismus: WorldBorder-Plugin/Mod oder Command-Block-basiertes Setup (20x20m Radius, Adventure Mode).Freigabe-Trigger: Skript oder Web-UI-Aktion zum Umschalten auf Survival und Entfernen der Border/Restriktion.2.3 Whitelist Manager Web-UIAnbindung: Zugriff auf die Server-Konsole via RCON oder direkte Bearbeitung der whitelist.json im Docker-Volume.Interface: Minimalistische Web-Oberfläche (z. B. Flask/Node.js oder direkte API) zur Whitelist-Pflege durch Admin/User.3. Architektur & Deployment3.1 Netzwerk & Proxy (Caddy)Caddy als Reverse Proxy für das Web-UI und Management-Endpunkte.Minecraft-Port (25565) direkt auf den Docker-Container durchgereicht.3.2 PhasenplanungPhase 1: Demo-ServerAufsetzen einer Testinstanz mit Standard-Settings.Validierung der Performance (RAM, CPU-Last) unter Last mit 1-2 Testspielern.Generierung und Auswahl des World-Seeds.Phase 2: Produktion & Waiting CageDeployment des Produktivservers.Implementierung der Start-Barriere (20x20m, Adventure-Modus).Integration des "Go!"-Mechanismus zum Startschuss.Phase 3: Web-UI & Whitelist ManagerBereitstellung der Whitelist-Verwaltung über das Web-UI.Finaler Funktionstest.
Ja, ein Grafana-Stack ist die **professionellere und skalierbarere Lösung** — und es gibt eine fertige NeoForge-1.21.1-Unterstützung. Hier ist der komplette Vergleich und Setup-Plan.

---

# Grafana-Stack für Enigmatica 10 — vollständiger Plan

## Entscheidung: Die richtige Komponente

Es gibt drei bekannte Wege, Minecraft-Metriken in Prometheus/Grafana zu bringen. Für **NeoForge 1.21.1** (E10) ist nur einer direkt geeignet:

| Lösung                                        | NeoForge 1.21.1?                  | TPS          | MSPT         | Weitere Metriken                                      | Export-Format         | Aufwand                              |
| --------------------------------------------- | --------------------------------- | ------------ | ------------ | ----------------------------------------------------- | --------------------- | ------------------------------------ |
| **`minecraft-prometheus-exporter`** (cpburnz) | ✅ **Ja — nativ!**                | ✅ via spark | ✅ via spark | Chunks, Entities, Spieler, JVM, Dimension-Tick-Zeiten | Prometheus `/metrics` | Gering — Mod rein, fertig            |
| `itzg/mc-monitor`                             | ✅ (server-extern)                | ❌ Nein      | ❌ Nein      | Nur: healthy, response-time, players online/max       | Prometheus            | Minimal — aber **keine TPS/MSPT**    |
| `ServerPulse`                                 | ❌ Nein (nur Bukkit/Paper/Fabric) | ✅           | ✅           | CPU, Disk, Memory, Entities, Chunks, Ping             | InfluxDB + Grafana    | Mittel — aber **nicht für NeoForge** |

### 🏆 Gewinner: `minecraft-prometheus-exporter` von cpburnz

**Warum:**

- **Explizite NeoForge 1.21.1-Unterstützung** — Release `1.21.1-neoforge-1.2.1` existiert
- Exportiert direkt im **Prometheus-Format** auf einem HTTP-`/metrics`-Endpunkt
- Sammelt **TPS, MSPT** (in Kombination mit spark), Dimension-Tick-Zeiten, Entities, Chunks, Spieler, JVM-Metriken
- Server-seitige Mod — muss nicht auf Clients installiert werden
- Mehrere **fertige Grafana-Dashboards** verfügbar (z.B. Dashboard ID 22017, aktualisiert für Grafana v11 )

> **`itzg/mc-monitor`** ist ein externer Container, der nur Server-Status (online/offline, Spielerzahl, Response-Time) via Server-List-Ping abfragt — er kann **keine TPS oder MSPT** liefern, da dafür Server-Interna nötig sind. Für deine Anforderungen also ungeeignet als alleinige Quelle.

> **`ServerPulse`** sieht toll aus (All-in-One mit InfluxDB + auto-provisioned Grafana-Dashboards), unterstützt aber **nur Bukkit/Spigot/Paper/Fabric** — nicht NeoForge oder Forge .

---

## Architektur: Kompletter Grafana-Stack

```
┌─────────┐   HTTPS    ┌─────────┐                 ┌──────────────────┐
│ Browser │ ─────────► │  Caddy  │ ──► Flask:5000  │  Web-UI          │
│         │   (443)    │         │ ──► Grafana:3000 │  • Whitelist     │
└─────────┘            └─────────┘                 │  • Donations     │
                                                   │  • Go!-Button    │
                                                   └────────┬─────────┘
                                                            │
                     ┌──────────────────────────────────────┘
                     │
                     ▼
              ┌──────────────┐    scrape     ┌──────────────────────┐
              │  Prometheus  │ ────────────► │  MC Server Container │
              │  (:9090)     │    /metrics   │  NeoForge 1.21.1     │
              └──────┬───────┘    alle 15s    │  + spark mod         │
                     │                       │  + prom-exporter mod │
                     │                       │  Exporter: :9150     │
                     ▼                       └──────────────────────┘
              ┌──────────────┐
              │   Grafana    │  ◄── Dashboard: TPS, MSPT, Players,
              │   (:3000)    │       Chunks, Entities, JVM, Memory
              └──────────────┘
```

**Datenfluss:**

1. **spark** sammelt TPS/MSPT im Server-Prozess
2. **minecraft-prometheus-exporter** liest spark-Daten + Server-Interna → exponiert `/metrics` auf Port 9150
3. **Prometheus** scrapt `/metrics` alle 15 Sekunden → speichert Zeitreihe
4. **Grafana** visualisiert Prometheus-Daten → fertiges MC-Dashboard
5. **Caddy** proxyt Grafana (und Flask-Web-UI) über HTTPS

---

## Docker Compose — erweitert um Grafana-Stack

```yaml
# docker-compose.yml — komplett (MC + Web-UI + Monitoring)
services:
  # ═══════════════════════════════════════
  # Minecraft Server (Enigmatica 10)
  # ═══════════════════════════════════════
  mc:
    image: itzg/minecraft-server
    container_name: e10-server
    restart: unless-stopped
    environment:
      EULA: "TRUE"
      TYPE: "CURSEFORGE"
      CF_SERVER_MODPACK: "https://www.curseforge.com/minecraft/modpacks/enigmatica10/download/6734671"
      CF_API_KEY: "${CF_API_KEY}"
      VERSION: "1.21.1"
      MEMORY: "12G"
      USE_AIKAR_FLAGS: "TRUE"
      ENABLE_WHITELIST: "TRUE"
      ENFORCE_WHITELIST: "TRUE"
      ENABLE_RCON: "TRUE"
      RCON_PASSWORD: "${RCON_PASSWORD}"
      TZ: "Europe/Berlin"
      # Mods automatisch laden:
      MODS: |
        https://cdn.modrinth.com/data/l6YH9tlS/versions/1.10.124-neoforge-1.21.1/spark-1.10.124-neoforge.jar,
        https://github.com/cpburnz/minecraft-prometheus-exporter/releases/download/1.21.1-neoforge-1.2.1/prometheus-exporter-1.21.1-neoforge-1.2.1.jar
    volumes:
      - mc-data:/data
    ports:
      - "25565:25565" # Minecraft (direkt, nicht durch Caddy)
    # Port 9150 (Prometheus Exporter) NICHT öffentlich exponieren —
    # nur internes Docker-Netzwerk

  # ═══════════════════════════════════════
  # Prometheus — Metriken-Sammler
  # ═══════════════════════════════════════
  prometheus:
    image: prom/prometheus:latest
    container_name: e10-prometheus
    restart: unless-stopped
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    # InternOnly — nicht öffentlich

  # ═══════════════════════════════════════
  # Grafana — Visualisierung & Dashboards
  # ═══════════════════════════════════════
  grafana:
    image: grafana/grafana:latest
    container_name: e10-grafana
    restart: unless-stopped
    environment:
      GF_SECURITY_ADMIN_PASSWORD: "${GRAFANA_PASSWORD}"
      GF_USERS_ALLOW_SIGN_UP: "false"
      # Auto-provision Prometheus als Datenquelle:
      GF_DATASOURCES_PATH: "/etc/grafana/provisioning/datasources"
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus

  # ═══════════════════════════════════════
  # Flask Web-UI (Whitelist, Donations, Go!)
  # ═══════════════════════════════════════
  flask:
    build: ./webui
    container_name: e10-webui
    restart: unless-stopped
    environment:
      RCON_HOST: "mc"
      RCON_PORT: "25575"
      RCON_PASSWORD: "${RCON_PASSWORD}"
      KOFI_WEBHOOK_SECRET: "${KOFI_WEBHOOK_SECRET}"
      PROMETHEUS_URL: "http://prometheus:9090"
    depends_on:
      - mc

  # ═══════════════════════════════════════
  # Caddy — Reverse Proxy (HTTPS)
  # ═══════════════════════════════════════
  caddy:
    image: caddy:2
    container_name: e10-caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy-data:/data
    depends_on:
      - flask
      - grafana

volumes:
  mc-data:
  prometheus-data:
  grafana-data:
  caddy-data:
```

### `prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "minecraft"
    static_configs:
      - targets: ["mc:9150"] # minecraft-prometheus-exporter im MC-Container
    metrics_path: /metrics
```

### Grafana Datenquelle (auto-provisioned)

```yaml
# grafana/provisioning/datasources/prometheus.yml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

### Caddyfile — mit Grafana-Subpath

```caddyfile
mc-admin.{$DOMAIN} {
    # Web-UI (Whitelist, Donations, Go!)
    handle /api/* {
        reverse_proxy flask:5000
    }
    handle {
        reverse_proxy flask:5000
    }
}

grafana.{$DOMAIN} {
    # Grafana Dashboard — komplett separate Subdomain
    reverse_proxy grafana:3000
    basic_auth {
        admin <bcrypt-hash>
    }
}
```

---

## Exportierte Metriken (was du im Grafana siehst)

Der `minecraft-prometheus-exporter` liefert u.a. :

| Prometheus-Metrik                      | Bedeutung                                        | Für dich relevant?                           |
| -------------------------------------- | ------------------------------------------------ | -------------------------------------------- |
| `mc_server_tick_seconds`               | **MSPT** — Sekunden pro Tick                     | ✅ Ja — Kernmetrik                           |
| `mc_dimension_tick_seconds{id, name}`  | Tick-Zeit pro Dimension (overworld, nether, end) | ✅ Sehr nützlich — lag in welchem Dimension? |
| `mc_player_list{id, name}`             | Online-Spieler                                   | ✅                                           |
| `mc_entities_total{dim, type}`         | Entities pro Dimension/Typ                       | ✅ Lag-Diagnose                              |
| `mc_dimension_chunks_loaded{id, name}` | Geladene Chunks pro Dimension                    | ✅                                           |
| JVM-Metriken (Memory, GC)              | Java-Heap, GC-Pausen                             | ✅ Memory-Leak-Erkennung                     |

> TPS wird berechnet aus `mc_server_tick_seconds`: **TPS = min(20, 1 / tick_seconds)**. Alternativ über spark's TPS-Werte, falls der Exporter diese direkt liefert (abhängig von spark-Integration).

### Fertige Grafana-Dashboards

| Dashboard                                 | ID        | Quelle                        |
| ----------------------------------------- | --------- | ----------------------------- |
| Minecraft Server (v11, aktualisiert 2024) | **22017** | cpburnz exporter, Grafana v11 |
| Minecraft Modded 1.20.1 Forge             | 20659     | Modded-spezifisch             |
| Minecraft Server Stats                    | 16508     | Allgemein                     |

> **Import:** In Grafana → Dashboards → Import → Dashboard-ID `22017` eingeben → Prometheus als Datenquelle wählen → fertig. Dashboard wird automatisch geladen.

---

## Custom TPS/MSPT-Widget im Flask-Web-UI

Wenn du die Live-Werte **auch direkt im Web-UI** willst (ohne Grafana öffnen zu müssen), fragt Flask einfach Prometheus ab:

```python
# Flask: Live-Metriken aus Prometheus abfragen
import requests

PROMETHEUS = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")

@app.get("/api/metrics/now")
def metrics_now():
    # MSPT (Median Tick-Zeit) aus Prometheus abfragen
    resp = requests.get(f"{PROMETHEUS}/api/v1/query", params={
        "query": "rate(mc_server_tick_seconds_sum[30s]) / rate(mc_server_tick_seconds_count[30s])"
    }).json()
    mspt_seconds = float(resp["data"]["result"][0]["value"][1]) if resp["data"]["result"] else 0
    mspt_ms = mspt_seconds * 1000
    tps = min(20, 1000 / mspt_ms) if mspt_ms > 0 else 20

    return jsonify({
        "tps": round(tps, 1),
        "mspt": round(mspt_ms, 1),
        "idle_ms": round(max(0, 50 - mspt_ms), 1)
    })

@app.get("/api/metrics/history")
def metrics_history():
    """TPS/MSPT über letzte 6h für Graph im Web-UI"""
    resp = requests.get(f"{PROMETHEUS}/api/v1/query_range", params={
        "query": "rate(mc_server_tick_seconds_sum[1m]) / rate(mc_server_tick_seconds_count[1m]) * 1000",
        "start": time.time() - 6 * 3600,
        "end": time.time(),
        "step": "60s"
    }).json()

    points = []
    for item in resp["data"]["result"]:
        for ts, val in item["values"]:
            mspt = float(val)
            points.append({
                "ts": int(ts),
                "mspt": round(mspt, 1),
                "tps": round(min(20, 1000 / mspt), 1) if mspt > 0 else 20,
                "idle_ms": round(max(0, 50 - mspt), 1)
            })
    return jsonify(points)
```

> So hast du **beides**: ein vollwertiges Grafana-Dashboard (für tiefere Analysen, Historisierung, Alerts) **und** ein kompakteres Live-Widget im Web-UI (für Spieler/Admin-Quick-Check).

---

## Vergleich: Custom-Lösung (Chart.js) vs. Grafana-Stack

| Kriterium           | Custom (Chart.js + SQLite) | **Grafana-Stack**                                        |
| ------------------- | -------------------------- | -------------------------------------------------------- |
| Setup-Aufwand       | Mittel (selber bauen)      | Initial höher (3 Container mehr)                         |
| Wartung             | Eigene Code-Pflege         | Standard-Tools, Community-Support                        |
| Historisierung      | SQLite (selber prunen)     | **Prometheus (auto-retention, komprimiert)**             |
| Dashboards          | Selbst bauen               | **Fertige MC-Dashboards importierbar**                   |
| Alerts              | Selbst bauen               | **Grafana Alerting** (Discord/Webhook bei TPS < 15)      |
| Skalierbarkeit      | Limitiert                  | **Beliebig erweiterbar** (Node-Exporter, cAdvisor, etc.) |
| Ressourcen-Overhead | Minimal                    | ~500 MB RAM für Prometheus + Grafana                     |
| Lernkurve           | Flach (Flask/JS)           | Mittel (PromQL lernen)                                   |
| Professionalität    | OK                         | **Professioneller Standard**                             |

### Ressourcen-Bedarf des Grafana-Stacks

| Komponente         | RAM (ca.)       | CPU                       |
| ------------------ | --------------- | ------------------------- |
| Prometheus         | ~200–300 MB     | Minimal (scrape alle 15s) |
| Grafana            | ~150–250 MB     | Minimal                   |
| **Total Overhead** | **~400–550 MB** | Vernachlässigbar          |

> Bei 12 GB RAM für den MC-Server und einem dedizierten Host ist das **kein Problem**. Der Overhead ist < 5% deines RAM-Budgets.

---

## Empfehlung & Phasenplan-Update

### 🏆 Empfehlung: **Grafana-Stack mit `minecraft-prometheus-exporter`**

**Warum nicht nur Custom:**

- Du bekommst **professionelle Dashboards out-of-the-box** statt selbst Chart.js-Graphen zu bauen
- **Alerting** ist trivial (Grafana → Discord-Webhook bei TPS < 15)
- **Prometheus übernimmt Historisierung** — keine SQLite-Pruning-Logik nötig
- Erweiterbar: später `node-exporter` (Host-CPU/RAM) oder `cAdvisor` (Docker-Stats) hinzufügen = 1 Zeile in `prometheus.yml`

**Warum trotzdem Flask-Web-UI behalten:**

- Für Whitelist-Management, Donation-Counter, Go!-Button
- Kompakter Live-TPS-Widget (Prometheus abfragend) für Quick-Glance ohne Grafana

### Phasenplan — final aktualisiert

| Phase             | Tasks (neu/hinzugefügt)                                                                                                                                                  |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **1: Demo**       | spark + `minecraft-prometheus-exporter` Mod installieren; Prometheus + Grafana Container starten; Dashboard ID 22017 importieren; TPS/MSPT-Verlauf unter Last validieren |
| **2: Produktion** | Grafana-Alerts einrichten (TPS < 15 → Discord-Webhook); Waiting Cage via RCON; Caddy-Routing für `grafana.domain.de`                                                     |
| **3: Web-UI**     | Flask `/api/metrics/now` + `/api/metrics/history` (Prometheus-Queries); Live-TPS-Widget im Web-UI; Ko-fi Donation-Counter; finaler Funktionstest                         |

### ⚠️ Praktische Hinweise

1. **Port 9150 (Exporter) nicht öffentlich exponieren** — nur im Docker-Netzwerk für Prometheus erreichbar. Exponierst du ihn, kann jeder deine Server-Metriken lesen.
2. **Grafana hinter Caddy + Basic Auth** — Grafana hat eigenes Auth, aber Caddy-Basic-Auth als zusätzliche Schicht schützt vor Bots.
3. **Prometheus Retention** — Default 15 Tage. Für längere Historie: `--storage.tsdb.retention.time=90d` in Prometheus-Command.
4. **Dashboard 22017** ist für den `cpburnz/minecraft-prometheus-exporter` gemacht — perfekt kompatibel.
5. **`MODS`-Environment-Variable** bei `itzg/minecraft-server` lädt JARs automatisch aus URLs in den `/data/mods`-Ordner — spark + Exporter werden so beim Container-Start automatisch installiert.
   Hier ist die ausgearbeitete Erweiterung deines Projektplans um **Donations** und **Live-Server-Metriken (TPS/MSPT-Graph)**.

---

# Erweiterung: Donations & Live-Server-Metriken

## 1. Donation-Integration

### ⚠️ Wichtiger Vorab-Hinweis: "Sofortüberweisung"

Die klassische **Sofortüberweisung wurde am 30. September 2024 eingestellt** und in **Klarna Pay Now** integriert [^1]. Seit 2025/2026 ist in der EU zudem **SEPA Instant Credit Transfer (SCT Inst)** der neue Standard — Überweisungen in <10 Sekunden, 24/7, gesetzlich verordnet [^5]. Was du heute als "Sofortüberweisung" kennst, läuft also entweder über **Klarna** oder **SEPA Instant** (via Stripe).

### Anbieter-Vergleich

| Anbieter                 | PayPal          | Apple Pay                                      | Google Pay       | SEPA/Klarna (EU)                                            | Gebühren                                                          | Embed-Widget                     | Donation Counter                           |
| ------------------------ | --------------- | ---------------------------------------------- | ---------------- | ----------------------------------------------------------- | ----------------------------------------------------------------- | -------------------------------- | ------------------------------------------ |
| **Ko-fi**                | ✅              | ✅ (via Stripe) [^6]                           | ✅               | ✅ (via Stripe — SEPA, Klarna, iDEAL etc. automatisch) [^3] | **0% Plattform-Fee** (nur PayPal/Stripe-Verarbeitungsgebühr) [^7] | ✅ Tip-Widget (embeddable) [^10] | ❌ Native: nein (via Webhook selbst bauen) |
| **Polar.sh**             | ✅ (via Stripe) | ✅ (embedded: Domain-Verifizierung nötig) [^4] | ✅               | ✅ (Stripe-basiert, SEPA etc.)                              | **5% + 50¢** (Starter, ab Mai 2026) [^11]                         | ✅ Embedded Checkout [^4]        | ❌ Selbst bauen                            |
| **PayPal Donate Button** | ✅              | ✅ (Apple Pay via PayPal checkout)             | ⚠️ Eingeschränkt | ❌ Kein SEPA/Klarna direkt                                  | ~2.49% + fest [^8]                                                | ✅ Pop-up Button                 | ❌                                         |

### 🏆 Empfehlung: **Ko-fi**

**Warum Ko-fi der beste Fit für dein Projekt ist:**

- **0% Plattform-Fee** — nur die PayPal/Stripe-Verarbeitungsgebühr (~2.9% + 30¢) fällt an [^7]
- **Alle geforderten Zahlungsmethoden** über eine einzige Integration:
  - PayPal (direkt verbunden) [^3]
  - Apple Pay (via Stripe, nur Stripe-Konto nötig) [^6]
  - Google Pay, SEPA, Klarna Pay Now (ehem. Sofortüberweisung), iDEAL etc. — alles **automatisch via Stripe** ohne Extra-Setup [^3]
- **Embeddable Tip-Widget** — einbetten auf deiner Web-UI per Script-Tag [^10]

**Einrichtung:**

1. Account auf ko-fi.com erstellen
2. PayPal-Konto + Stripe-Konto verbinden (Stripe aktiviert Apple Pay, Google Pay, SEPA, Klarna etc. automatisch)
3. Ko-fi Tip-Widget in die Web-UI einbetten

### Donation Counter Implementierung

Ko-fi bietet **Webhooks** für eingehende Spenden. Der Counter wird selbst gebaut:

```python
# Flask: Donation Counter via Ko-fi Webhook
from flask import Flask, request, jsonify
import json, os

app = Flask(__name__)
KOFI_WEBHOOK_SECRET = os.environ["KOFI_WEBHOOK_SECRET"]
TOTAL_FILE = "/data/donations_total.json"

def load_total():
    try:
        with open(TOTAL_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return {"total_cents": 0, "count": 0, "goal_cents": 50000}

def save_total(data):
    with open(TOTAL_FILE, "w") as f:
        json.dump(data, f)

@app.post("/api/kofi-webhook")
def kofi_webhook():
    # Ko-fi sends: { "data": "<urlencoded json>" }
    payload = json.loads(request.form["data"])
    if payload.get("verification_token") != KOFI_WEBHOOK_SECRET:
        return "Forbidden", 403

    data = load_total()
    data["total_cents"] += int(float(payload["amount"]) * 100)
    data["count"] += 1
    save_total(data)
    return "OK", 200

@app.get("/api/donations")
def get_donations():
    data = load_total()
    return jsonify({
        "total_eur": data["total_cents"] / 100,
        "count": data["count"],
        "goal_eur": data["goal_cents"] / 100,
        "progress_pct": min(100, (data["total_cents"] / data["goal_cents"]) * 100)
    })
```

**Frontend ( Donation Counter + Button ):**

```html
<!-- Ko-fi Button (embeddable widget) -->
<script src="https://storage.ko-fi.com/cdn/scripts/overlay-widget.js"></script>
<script>
  kofiWidgetOverlay.draw("dein-ko-fi-name", {
    type: "floating-chat",
    "floating-chat.donateButton.text": "Spenden",
    "floating-chat.donateButton.background-color": "#00b9fe",
    "floating-chat.donateButton.text-color": "#fff",
  });
</script>

<!-- Donation Counter (Custom) -->
<div class="donation-counter">
  <h3>Server-Spenden 🎯</h3>
  <div class="progress-bar">
    <div class="progress-fill" id="progress-fill"></div>
  </div>
  <p><span id="donated">0,00 €</span> von <span id="goal">500,00 €</span></p>
  <p><span id="donor-count">0</span> Spender</p>
</div>

<script>
  async function updateDonations() {
    const res = await fetch("/api/donations");
    const data = await res.json();
    document.getElementById("donated").textContent = data.total_eur.toFixed(2) + " €";
    document.getElementById("goal").textContent = data.goal_eur.toFixed(2) + " €";
    document.getElementById("donor-count").textContent = data.count;
    document.getElementById("progress-fill").style.width = data.progress_pct + "%";
  }
  updateDonations();
  setInterval(updateDonations, 30000); // alle 30s aktualisieren
</script>
```

> **Webhook-Setup:** Ko-fi Webhook-URL = `https://mc-admin.deine-domain.de/api/kofi-webhook` (durch Caddy TLS-terminiert). In Ko-fi unter "Webhooks" eintragen + Verification Token setzen.

---

## 2. Live-Server-Metriken: TPS & MSPT-Graph

### spark Mod — Die Lösung

**spark** ist der Community-Standard-Profiler für Minecraft (200M+ Downloads) und unterstützt **NeoForge 1.21.1** nativ [^9]. Verfügbar für E10/MC 1.21.1 als Version **1.10.124 (NeoForge 1.21.1)** [^12].

**Was spark liefert:**

| Metrik                             | Beschreibung                         | Quelle |
| ---------------------------------- | ------------------------------------ | ------ |
| **TPS** (5s, 10s, 1m, 5m, 15m)     | Ticks per second — ideal: 20.0 TPS   |        |
| **MSPT** (min, med, max, 95th pct) | Milliseconds per tick — ideal: ≤50ms |        |
| CPU%, Memory, Disk                 | System-Metriken                      |        |

> **Wichtig:** Bei Docker-Containern kann spark CPU/Memory teilweise falsch melden (bekanntes Issue) — TPS und MSPT sind aber davon **nicht** betroffen und zuverlässig.

### Datenabruf: Zwei Wege

#### Weg A: spark Developer API (Java) — empfohlen für Genauigkeit

spark hat eine **Java Developer API**, die TPS/MSPT direkt auslesen lässt. Da dein Flask-Backend aber Python ist und nicht im JVM-Prozess läuft, ist dieser Weg nur über eine **eigene kleine NeoForge-Mod** machbar, die die spark-API nutzt und einen HTTP-Endpunkt exponiert.

#### Weg B: RCON + `/spark tps` parsen — einfachster Weg

```python
import re, json, mcrcon as mc

def get_spark_metrics(rcon_host, rcon_pass, rcon_port=25575):
    with mc.MCRcon(rcon_host, rcon_pass, port=rcon_port) as r:
        tps_resp = r.command("spark tps")
        # spark output parsen — enthält TPS (5s/10s/1m/5m/15m) + MSPT

    # Parse TPS values (Format: "TPS from last 5s, 10s, 1m, 5m, 15m: 20.0, 20.0, 19.8, 19.5, 19.7")
    tps_match = re.search(r'(\d+\.?\d*),\s*(\d+\.?\d*),\s*(\d+\.?\d*),\s*(\d+\.?\d*),\s*(\d+\.?\d*)', tps_resp)
    mspt_match = re.search(r'MSPT.*?(\d+\.?\d*).*?(\d+\.?\d*).*?(\d+\.?\d*)', tps_resp)

    return {
        "tps": {
            "5s": float(tps_match.group(1)),
            "10s": float(tps_match.group(2)),
            "1m": float(tps_match.group(3)),
            "5m": float(tps_match.group(4)),
            "15m": float(tps_match.group(5)),
        },
        "mspt": {
            "min": float(mspt_match.group(1)),
            "med": float(mspt_match.group(2)),
            "max": float(mspt_match.group(3)),
        },
        "idle_ms": max(0, 50 - float(mspt_match.group(2))),  # Zeit übrig pro Tick
        "timestamp": time.time()
    }
```

> **Nachteil:** RCON-Polling alle paar Sekunden erzeugt Console-Spam. Besser: **eigene Mini-Mod** (Weg A) oder **Spark-REST** (Community-Mod, die spark-Daten via HTTP exponiert — aber derzeit nur für Forge 1.20.1, nicht NeoForge 1.21 [^2]).

#### Weg C: Eigene Mini-NeoForge-Mod (sauberste Lösung)

Eine ~50-Zeilen-Mod, die spark's Developer API nutzt und einen HTTP-Server im Server-Prozess startet:

```java
// Minimal: spark metrics HTTP endpoint
// Build against spark API + NeoForge 1.21.1
public class MetricsEndpoint {
    @SubscribeEvent
    public void onServerStarted(ServerStartedEvent event) {
        var server = event.getServer();
        var spark = SparkProvider.get();  // spark Developer API

        Javalin.create()
            .get("/metrics", ctx -> {
                var tps = spark.getStatistics().getTps();       // double[] (5s, 10s, 1m, 5m, 15m)
                var mspt = spark.getStatistics().getMspt();     // double[] (min, med, max)
                ctx.json(Map.of(
                    "tps", tps,
                    "mspt", mspt,
                    "idle_ms", Math.max(0, 50 - mspt[1]),
                    "timestamp", System.currentTimeMillis()
                ));
            })
            .start(25580);  // nur intern im Docker-Netzwerk
    }
}
```

> Die spark Developer API stellt ein `Spark`-Interface bereit, über das `getStatistics()` TPS und MSPT als Arrays liefert. Container-intern auf Port 25580, vom Flask-Backend abgefragt.

### Historisierung & Graph

**Flask: SQLite als Zeitreihen-Speicher**

```python
import sqlite3, time, threading

DB = "/data/metrics.db"

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS metrics (
        ts REAL, tps_5s REAL, tps_10s REAL, tps_1m REAL, tps_5m REAL, tps_15m REAL,
        mspt_min REAL, mspt_med REAL, mspt_max REAL, idle_ms REAL
    )""")
    conn.commit()
    conn.close()

def poll_metrics_loop(spark_url="http://mc:25580/metrics"):
    while True:
        try:
            r = requests.get(spark_url, timeout=5).json()
            conn = sqlite3.connect(DB)
            conn.execute("INSERT INTO metrics VALUES (?,?,?,?,?,?,?,?,?,?)",
                (r["timestamp"], *r["tps"].values(), *r["mspt"].values(), r["idle_ms"]))
            conn.commit()
            conn.close()
        except: pass
        time.sleep(5)  # alle 5 Sekunden

# In Thread starten
threading.Thread(target=poll_metrics_loop, daemon=True).start()

@app.get("/api/metrics/history")
def metrics_history():
    """Letzte N Messpunkte für den Graphen"""
    hours = request.args.get("hours", 6, type=int)
    cutoff = time.time() - hours * 3600
    conn = sqlite3.connect(DB)
    rows = conn.execute(
        "SELECT ts, tps_10s, mspt_med, idle_ms FROM metrics WHERE ts > ? ORDER BY ts",
        (cutoff,)
    ).fetchall()
    conn.close()
    return jsonify([{
        "ts": row[0], "tps": row[1], "mspt": row[2], "idle_ms": row[3]
    } for row in rows])

@app.get("/api/metrics/now")
def metrics_now():
    """Aktuelle Werte für Live-Anzeige"""
    conn = sqlite3.connect(DB)
    row = conn.execute(
        "SELECT tps_10s, mspt_med, idle_ms FROM metrics ORDER BY ts DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if not row: return jsonify({"tps": 20, "mspt": 0, "idle_ms": 50})
    return jsonify({"tps": row[0], "mspt": row[1], "idle_ms": row[2]})
```

**Frontend-Graph (mit Chart.js):**

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<div class="server-stats">
  <div class="stat-cards">
    <div class="card">TPS: <span id="tps-now">20.0</span> / 20</div>
    <div class="card">MSPT: <span id="mspt-now">5</span> ms</div>
    <div class="card">Idle: <span id="idle-now">45</span> ms/tick</div>
  </div>
  <canvas id="tps-chart" height="200"></canvas>
  <canvas id="mspt-chart" height="200"></canvas>
</div>

<script>
  const tpsChart = new Chart(document.getElementById("tps-chart"), {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "TPS",
          data: [],
          borderColor: "#00b9fe",
          tension: 0.3,
          yAxis: { min: 0, max: 20 },
        },
      ],
    },
    options: {
      scales: { y: { min: 0, max: 21 } },
      plugins: { title: { display: true, text: "TPS über Zeit (10s-Durchschnitt)" } },
    },
  });

  const msptChart = new Chart(document.getElementById("mspt-chart"), {
    type: "line",
    data: {
      labels: [],
      datasets: [
        { label: "MSPT", data: [], borderColor: "#ff6b6b", tension: 0.3 },
        { label: "Idle (ms übrig)", data: [], borderColor: "#51cf66", tension: 0.3 },
      ],
    },
    options: {
      plugins: { title: { display: true, text: "MSPT & Idle-Zeit pro Tick" } },
    },
  });

  async function updateCharts() {
    const res = await fetch("/api/metrics/history?hours=6");
    const data = await res.json();

    const labels = data.map((d) => new Date(d.ts * 1000).toLocaleTimeString());
    tpsChart.data.labels = labels;
    tpsChart.data.datasets[0].data = data.map((d) => d.tps);
    tpsChart.update("none");

    msptChart.data.labels = labels;
    msptChart.data.datasets[0].data = data.map((d) => d.mspt);
    msptChart.data.datasets[1].data = data.map((d) => d.idle_ms);
    msptChart.update("none");

    // Live-Werte
    const now = data[data.length - 1];
    if (now) {
      document.getElementById("tps-now").textContent = now.tps.toFixed(1);
      document.getElementById("mspt-now").textContent = now.mspt.toFixed(0);
      document.getElementById("idle-now").textContent = now.idle_ms.toFixed(0);
    }
  }

  updateCharts();
  setInterval(updateCharts, 5000); // alle 5s aktualisieren
</script>
```

### Spark-Mod Installation in Docker

spark als Mod zum Enigmatica-10-Container hinzufügen:

```yaml
# docker-compose.yml — ergänzt
services:
  mc:
    environment:
      # ... bestehende Config ...
      # spark Mod automatisch herunterladen:
      MODS: "https://cdn.modrinth.com/data/l6YH9tlS/versions/1.10.124-neoforge-1.21.1/spark-1.10.124-neoforge.jar"
      # Oder Datei manuell ins /data/mods Volume legen
```

> spark 1.10.124 für NeoForge 1.21.1 ist auf Modrinth und CurseForge verfügbar [^12][^13].

---

## 3. Architektur-Update (komplettes Bild)

```
┌─────────┐    HTTPS     ┌─────────┐                ┌──────────────┐
│ Browser │ ───────────► │  Caddy  │ ──► Flask:5000 │  Web-UI      │
│         │   (443)      │         │                │  • Whitelist │
└─────────┘              └─────────┘                │  • Go!-Button│
                                                     │  • Donations │
                                                     │  • TPS-Graph │
                                                     └──┬───┬───┬───┘
                                                        │   │   │
                              RCON (25575) ─────────────┘   │   │
                              HTTP (25580, spark) ─────────┘   │
                              SQLite (metrics.db) ────────────┘
                                                        │
                     ┌──────────────┐                   │
                     │  MC Server   │ ◄─────────────────┘
                     │  (NeoForge)  │
                     │  + spark mod │
                     │  Port 25565  │
                     └──────────────┘
                           ▲
                           │ RCON: whitelist add/remove, worldborder, gamemode
                           │ spark: /metrics HTTP endpoint

┌─────────┐    Webhook    ┌─────────┐
│  Ko-fi  │ ───────────►  │  Flask  │ ──► SQLite: donations_total.json
│ PayPal  │   (HTTPS)     │ /kofi-  │
│ Apple   │               │ webhook │
│ Pay     │               └─────────┘
│ Klarna  │
│ SEPA    │
└─────────┘
```

---

## 4. Zusammenfassung: Was du brauchst

| Feature                                              | Lösung                                                        | Aufwand                                              |
| ---------------------------------------------------- | ------------------------------------------------------------- | ---------------------------------------------------- |
| **Donation Button** (PayPal, Apple Pay, SEPA/Klarna) | Ko-fi Tip-Widget (embedded) — 0% Plattform-Fee                | Klein (Account + Stripe verbinden, Script einbetten) |
| **Donation Counter**                                 | Ko-fi Webhook → Flask → SQLite → Frontend                     | Mittel (~50 LOC Backend + Frontend)                  |
| **Live TPS/MSPT**                                    | spark Mod (NeoForge 1.21.1) + Mini-HTTP-Mod oder RCON-Parsing | Mittel (spark installieren + Polling)                |
| **TPS/MSPT-Graph über Zeit**                         | Flask: SQLite-Zeitreihen + Chart.js Frontend                  | Mittel (~80 LOC Backend + Frontend)                  |
| **"Zeit übrig pro Tick"**                            | Berechnet: `max(0, 50 - MSPT)`                                | Trivial (in Metriken-Endpoint)                       |

### Phasenplan-Ergänzung

| Phase             | Neue Tasks                                                                                     |
| ----------------- | ---------------------------------------------------------------------------------------------- |
| **1: Demo**       | spark Mod installieren, Metriken-Polling testen, `/spark tps` via RCON validieren              |
| **2: Produktion** | Mini-HTTP-Mod deployen (oder RCON-Polling), SQLite-Historisierung starten                      |
| **3: Web-UI**     | Ko-fi einrichten + Webhook, Donation Counter + TPS-Graph in UI integrieren, Chart.js einbinden |

### ⚠️ Praktische Hinweise

1. **RCON-Polling Frequenz:** Alle 5 Sekunden `/spark tps` ist OK, aber erzeugt Console-Logs. Bei der Mini-Mod-Lösung (HTTP-Endpunkt) gibt es keinen Console-Spam.
2. **SQLite-Größe:** Bei 5-Sekunden-Intervall = ~17.280 Zeilen/Tag = ~1 MB/Tag. Auto-Prune auf z.B. 30 Tage empfohlen (`DELETE FROM metrics WHERE ts < ?`).
3. **Ko-fi Webhook benötigt HTTPS** — Caddy stellt das Zertifikat automatisch (Let's Encrypt).
4. **Apple Pay in Embedded Widgets** (Polar.sh) erfordert Domain-Verifizierung [^4] — bei Ko-fi ist Apple Pay über das Tip-Widget einfacher (nur Stripe-Konto nötig [^6]).
5. **Sofortüberweisung → Klarna Pay Now:** Wenn deutsche Spender "Sofort" sehen wollen, erscheint das bei Ko-fi/Stripe automatisch als **Klarna** oder **SEPA Instant** — der Name "Sofort" existiert nicht mehr [^1].

**References**

[^1]: [Local Payment Methods in Europe: SEPA Instant, iDEAL ...](https://tazapay.com/blog/local-payment-methods-europe) (16%)

[^2]: [GitHub - JonayKB/Spark-REST](https://github.com/JonayKB/Spark-REST) (12%)

[^3]: [What payment methods are available on Ko-fi? – Ko-fi Help](https://help.ko-fi.com/hc/en-us/articles/24482435253661-What-payment-methods-are-available-on-Ko-fi) (11%)

[^4]: [Embedded Checkout - Polar](https://polar.sh/docs/features/checkout/embed) (9%)

[^5]: [What are instant payments? - European Central Bank](https://www.ecb.europa.eu/paym/retail/instant_payments/html/index.en.html) (8%)

[^6]: [Offer Apple Pay to your supporters - Ko-fi Help](https://help.ko-fi.com/hc/en-us/articles/360017645677-Offer-Apple-Pay-to-your-supporters) (8%)

[^7]: [Donate on Ko-fi without a debit or credit card](https://getsby.com/en/creator-platform/donate-on-ko-fi-without-a-debit-or-credit-card/) (8%)

[^8]: [Donate Button](https://www.paypal.com/donate/buttons) (6%)

[^9]: [spark - Minecraft Mods - CurseForge](https://www.curseforge.com/minecraft/mc-mods/spark) (6%)

[^10]: [Ko-fi tip widget](https://help.ko-fi.com/hc/en-us/articles/360018381678-Ko-fi-tip-widget) (5%)

[^11]: [Pricing - Polar](https://polar.sh/resources/pricing) (4%)

[^12]: [spark - 1.10.124 (NeoForge 1.21.1) - Minecraft Mods - CurseForge](https://www.curseforge.com/minecraft/mc-mods/spark/files/6225208) (4%)

[^13]: [1.10.124-neoforge-1.21.1 - spark](https://modrinth.com/mod/spark/version/1.10.124-neoforge-1.21.1) (3%)
