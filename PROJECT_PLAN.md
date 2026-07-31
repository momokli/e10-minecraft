# Project Plan — Enigmatica 10

## Phase 1: Demo & Setup
- [ ] Deploy E10 test instance on projectmellon.de
- [ ] Validate performance (12G RAM, Java 21)
- [ ] Test world generation, explore seed options
- [ ] Install spark + prometheus-exporter mods
- [ ] Set up Grafana + Prometheus containers
- [ ] Import dashboard (TBD)
- [ ] Add simple whitelist via Web-UI
- [ ] SRV DNS: `e10.projectmellon.de` → `projectmellon.de:$PORT`

## Phase 2: Production
- [ ] Waiting Cage (WorldBorder 20x20, Adventure)
- [ ] Go!-Button (RCON: adventure→survival, border→max)
- [ ] Discord bridge (chat + join/leave)
- [ ] Bluemap or Dynmap setup
- [ ] Daily backup cron
- [ ] HTTPS → HTTP redirect for e10.projectmellon.de
- [ ] Grafana alerts (TPS < 15 → Discord webhook)

## Phase 3: Polish
- [ ] Donation page (Ko-fi embed)
- [ ] Server MOTD & status page
- [ ] Performance tuning
- [ ] Blueprint world (future)
