# Deployment — Enigmatica 10

## Prerequisites

- `ssh projectmellon.de` must work without password
- Docker with `compose` plugin installed on server
- `borgbackup` on server for cron-based backups
- Environment variables: `CF_API_KEY`, `RCON_PASSWORD`, `GRAFANA_PASSWORD`, `CLOUDFLARE_API_TOKEN`

## Quick Deploy

```bash
# 1. Pause old servers to free RAM
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/pause-homestead.yml

# 2. Deploy everything
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy.yml
```

## Architecture

```
/srv/e10/
├── test/
│   ├── compose.yaml    # MC-TEST (6G, port 25580)
│   └── data/
├── prod/
│   ├── compose.yaml    # MC-PROD (12G, port 25585)
│   └── data/
└── shared/
    ├── compose.yaml    # Prometheus, Grafana, Web-UI, Caddy
    ├── webui/
    ├── prometheus/
    └── grafana/
```

## Useful Commands

```bash
# Logs (all instances)
journalctl -t e10-prod -t e10-test -t e10-shared -f

# Specific instance
journalctl -t e10-prod -f

# Backup
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/backup.yml

# Restore (interactive)
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/restore.yml

# Rollback (latest backup)
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/rollback.yml

# Update modpack
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/update.yml
```

## Web-UI

- **URL:** https://e10.projectmellon.de
- **Features:** Player list, whitelist management, MOTD, backups, RCON commands
- **Instances:** Switch between PROD and TEST via tabs

## Grafana

- **URL:** https://grafana.e10.projectmellon.de
- **User:** admin
- **Password:** `$GRAFANA_PASSWORD`

## Cron Backups (on server)

```bash
# Add to crontab on projectmellon.de:
# Every 30 minutes
*/30 * * * * cd /srv/e10 && ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/backup.yml
```

Or install borg on the host and run directly:

```bash
# Every 30 minutes for PROD
*/30 * * * * borg create --stats --compression lz4 /srv/e10/prod/backups::prod-$(date +\%Y\%m\%d-\%H\%M\%S) /srv/e10/prod/data/world && borg prune --keep-hourly 48 --keep-daily 30 --keep-weekly 12 /srv/e10/prod/backups

# Every 30 minutes for TEST
*/30 * * * * borg create --stats --compression lz4 /srv/e10/test/backups::test-$(date +\%Y\%m\%d-\%H\%M\%S) /srv/e10/test/data/world && borg prune --keep-hourly 48 --keep-daily 30 --keep-weekly 12 /srv/e10/test/backups
```

## DNS (Cloudflare)

SRV records are created automatically by the deploy playbook. Manual fallback:

```bash
# Zone: projectmellon.de (ID: 70505a13081de0743e8e7fbae48d6611)

# SRV record for PROD
curl -X POST -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  "https://api.cloudflare.com/client/v4/zones/70505a13081de0743e8e7fbae48d6611/dns_records" \
  -d '{"type":"SRV","name":"_minecraft._tcp.e10","data":{"priority":0,"weight":5,"port":25585,"target":"projectmellon.de"},"ttl":3600}'

# SRV record for TEST
curl -X POST -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  "https://api.cloudflare.com/client/v4/zones/70505a13081de0743e8e7fbae48d6611/dns_records" \
  -d '{"type":"SRV","name":"_minecraft._tcp.test.e10","data":{"priority":0,"weight":5,"port":25580,"target":"projectmellon.de"},"ttl":3600}'
```

## Caddy (on projectmellon.de)

Managed by Ansible deploy playbook. Manually in `/home/momo/Caddyfile`:

```caddy
e10.projectmellon.de {
    reverse_proxy 127.0.0.1:5000
}
grafana.e10.projectmellon.de {
    reverse_proxy 127.0.0.1:5000
}
```

Reload: `sudo systemctl restart caddy-planet.service`
