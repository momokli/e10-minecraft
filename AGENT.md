# Enigmatica 10 — Agent Context

## Project

- **Modpack:** Enigmatica 10 (E10) v1.30.0
- **MC Version:** 1.21.1
- **Loader:** NeoForge
- **Slug:** `enigmatica10`
- **Java:** 21 (itzg/minecraft-server:java21)
- **RAM:** 12 GB
- **Players:** 5–8 concurrent

## Domains

- `e10.projectmellon.de` — HTTP→HTTPS, custom MC port via SRV
- `grafana.e10.projectmellon.de` — Grafana behind Caddy
- DNS: Cloudflare API (`CLOUDFLARE_API_TOKEN` in env)

## Server (projectmellon.de)

- **Access:** `ssh projectmellon.de` — available from dev machine, no password needed
- **Path:** `/srv/e10`
- **Ports:** TEST=`25580`, PROD=`25585` (25565–25575 already in use)
- **RAM:** 62 GB total, ~17 GB free (after pausing homestead/homestead2 → ~33 GB free)
- **Storage:** 281 GB free on `/` (904 GB total)
- **Caddy:** `/home/momo/Caddyfile`, reload: `sudo systemctl restart caddy-planet.service`
- **Deploy:** `ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy.yml`
- **Logs:** `journalctl -t e10-prod -t e10-test -t e10-shared -f`

## Architecture

```
PROD: mc:25565 → host:25585 | SRV: _minecraft._tcp.e10 → projectmellon.de:25585
TEST: mc:25565 → host:25580 | SRV: _minecraft._tcp.test.e10 → projectmellon.de:25580
Caddy: e10.projectmellon.de → flask:5000
Caddy: grafana.e10.projectmellon.de → grafana:3000
```

### Server layout

```
/srv/e10/
├── test/
│   ├── compose.yaml   # MC-TEST (6G, port 25580)
│   ├── .env
│   ├── data/           # World, mods, config
│   └── backups/        # Borg repo
├── prod/
│   ├── compose.yaml   # MC-PROD (12G, port 25585)
│   ├── .env
│   ├── data/
│   └── backups/        # Borg repo
├── shared/
│   ├── compose.yaml   # Prometheus, Grafana, Web-UI
│   ├── webui/          # Flask app (manages both instances)
│   ├── prometheus/
│   └── grafana/
└── ansible/           # Playbooks & roles
```

## Monitoring

- `spark` + `minecraft-prometheus-exporter` → prometheus:9090 → grafana:3000

## API Keys & Tools

- **KAGI_API** — available in env. Usage documented in `e10/docs/kagi.md`
- **CF_API_KEY** — CurseForge API (in .env)
- **CLOUDFLARE_API_TOKEN** — DNS management (from env)
- **Sub-agents** — Prioritize for research, parallel tasks, and code review
- **Research** — Use Kagi API for web research, document findings in docs/

## Rules

- Ask before applying changes
- rcon-cli negative coords: `rcon-cli --password pw -- cmd arg1 -42 arg2`
- Worldborder max: `59999968`
- MOTD: 2 lines max

## Tasks

- [x] Find free ports: TEST=`25580`, PROD=`25585`
- [x] Evaluate server capacity (RAM, Storage)
- [x] Build Ansible playbooks (deploy, update, backup, restore, rollback)
- [x] Add spark + prometheus-exporter to compose
- [x] Create E2E test suite (`tests/e2e.py`)
- [x] Deploy PROD to projectmellon.de
- [x] Pause old servers: `ansible-playbook pause-homestead.yml`
- [ ] Run E2E tests after deployment
- [ ] Set up Borg backup cron job
- [ ] Import Grafana dashboard (TPS/MSPT)
- [ ] Discord bridge (chat + join/leave)
- [ ] Bluemap or Dynmap setup
- [ ] Add mod config tweaks (Waystones, Replica)

## Deployment Locations on projectmellon.de

- `/srv/` — Docker-based deployments (mc-homestead, mc-homestead2, factorio, etc.)
- `/home/momo/` — Some services (Caddyfile, personal scripts)
- **E10:** Target `/srv/e10` unless specified otherwise
