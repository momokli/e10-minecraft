#!/usr/bin/env python3
"""
E10 End-to-End Deployment Tests

Usage:
  python tests/e2e.py                     # Run all tests
  python tests/e2e.py --quick             # Quick MOTD + ping only
  python tests/e2e.py --instance prod     # Test only one instance

Requires:
  pip install mcstatus requests
"""

import argparse
import json
import socket
import sys
import time

import requests
from mcstatus import JavaServer

# ── Config ────────────────────────────────────────────────
SERVER = "projectmellon.de"
PROD_PORT = 25585
TEST_PORT = 25580
WEBUI_URL = "http://projectmellon.de:5002"
GRAFANA_URL = "http://projectmellon.de:3001"

INSTANCES = {
    "prod": {"port": PROD_PORT, "name": "PROD", "domain": "e10.projectmellon.de"},
    "test": {"port": TEST_PORT, "name": "TEST", "domain": "test.e10.projectmellon.de"},
}

PASS = 0
FAIL = 0
WARN = 0


# ── Helpers ───────────────────────────────────────────────


def ok(msg):
    global PASS
    PASS += 1
    print(f"  ✅ {msg}")


def fail(msg):
    global FAIL
    FAIL += 1
    print(f"  ❌ {msg}")


def warn(msg):
    global WARN
    WARN += 1
    print(f"  ⚠️  {msg}")


def banner(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


# ── Test Functions ────────────────────────────────────────


def test_tcp_reachable(host, port, label):
    """Can we open a TCP connection to the server?"""
    try:
        sock = socket.create_connection((host, port), timeout=10)
        sock.close()
        ok(f"{label} reachable on {host}:{port}")
        return True
    except Exception as e:
        fail(f"{label} NOT reachable on {host}:{port} — {e}")
        return False


def test_mc_status(host, port, label):
    """Query Minecraft server status (ping, MOTD, players)."""
    try:
        server = JavaServer.lookup(f"{host}:{port}")
        status = server.status()

        # Basic connectivity
        ok(f"{label} responded to status query ({status.latency:.0f}ms)")

        # Version
        print(f"     Version: {status.version.name}")

        # MOTD
        if status.motd:
            motd_text = status.motd.to_plain().strip()
            print(f"     MOTD: {repr(motd_text)}")
            if motd_text:
                ok(f"{label} MOTD is set")
            else:
                warn(f"{label} MOTD is empty")
        else:
            fail(f"{label} MOTD is missing")

        # Players
        print(f"     Players: {status.players.online}/{status.players.max}")
        ok(f"{label} player count reporting works")

        # Sample if players online
        if status.players.sample:
            names = [p.name for p in status.players.sample]
            print(f"     Sample: {', '.join(names)}")

        return status
    except Exception as e:
        fail(f"{label} MC status query failed — {e}")
        return None


def test_motd_format(host, port, label):
    """Check MOTD formatting (2 lines, visible colors)."""
    try:
        server = JavaServer.lookup(f"{host}:{port}")
        status = server.status()
        raw = status.motd.raw if hasattr(status.motd, "raw") else str(status.motd)
        plain = status.motd.to_plain().strip()
        lines = plain.split("\n")

        print(
            f"     Raw MOTD: {repr(raw) if len(raw) < 200 else repr(raw[:200]) + '...'}"
        )

        if len(lines) > 2:
            warn(f"{label} MOTD has {len(lines)} lines (max recommended: 2)")
        elif len(lines) == 2:
            ok(f"{label} MOTD is exactly 2 lines")
        elif len(lines) == 1:
            ok(f"{label} MOTD is 1 line")
        else:
            warn(f"{label} MOTD lines unclear")

        # Check for color codes
        if "§" in raw:
            ok(f"{label} MOTD uses color formatting codes")
    except Exception as e:
        fail(f"{label} MOTD format check failed — {e}")


def test_webui_accessible():
    """Check Web-UI is responding."""
    try:
        r = requests.get(WEBUI_URL, timeout=10, allow_redirects=True)
        if r.status_code == 200:
            ok(f"Web-UI accessible at {WEBUI_URL} (HTTP {r.status_code})")
            # Check it has the expected content
            if "Enigmatica 10" in r.text:
                ok("Web-UI contains expected title")
            else:
                warn("Web-UI loaded but title not found")
        else:
            fail(f"Web-UI returned HTTP {r.status_code}")
    except Exception as e:
        fail(f"Web-UI not accessible — {e}")


def test_webui_api(instance):
    """Test Web-UI API endpoints for a specific instance."""
    base = f"{WEBUI_URL}/api/{instance}"

    # Players endpoint
    try:
        r = requests.get(f"{base}/players", timeout=10)
        if r.status_code == 200:
            data = r.json()
            ok(f"Web-UI /api/{instance}/players → {len(data)} players")
        else:
            fail(f"Web-UI /api/{instance}/players → HTTP {r.status_code}")
    except Exception as e:
        fail(f"Web-UI /api/{instance}/players failed — {e}")

    # Whitelist endpoint
    try:
        r = requests.get(f"{base}/whitelist", timeout=10)
        if r.status_code == 200:
            data = r.json()
            ok(f"Web-UI /api/{instance}/whitelist → {len(data)} entries")
        else:
            fail(f"Web-UI /api/{instance}/whitelist → HTTP {r.status_code}")
    except Exception as e:
        fail(f"Web-UI /api/{instance}/whitelist failed — {e}")

    # MOTD endpoint
    try:
        r = requests.get(f"{base}/motd", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("raw"):
                ok(f"Web-UI /api/{instance}/motd → '{data['raw'][:60]}'")
            else:
                warn(f"Web-UI /api/{instance}/motd → empty")
        else:
            fail(f"Web-UI /api/{instance}/motd → HTTP {r.status_code}")
    except Exception as e:
        fail(f"Web-UI /api/{instance}/motd failed — {e}")


def test_grafana_accessible():
    """Check Grafana is responding."""
    try:
        r = requests.get(GRAFANA_URL, timeout=10, allow_redirects=True)
        if r.status_code == 200:
            ok(f"Grafana accessible at {GRAFANA_URL} (HTTP {r.status_code})")
        elif r.status_code == 401:
            ok(
                f"Grafana accessible at {GRAFANA_URL} (HTTP 401 = auth required, correct)"
            )
        else:
            fail(f"Grafana returned HTTP {r.status_code}")
    except Exception as e:
        fail(f"Grafana not accessible — {e}")


def test_dns_srv(domain):
    """Check SRV DNS record resolves correctly."""
    import subprocess

    try:
        result = subprocess.run(
            ["dig", "+short", "SRV", f"_minecraft._tcp.{domain}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.stdout.strip():
            ok(f"SRV record _minecraft._tcp.{domain} resolves: {result.stdout.strip()}")
        else:
            warn(
                f"SRV record _minecraft._tcp.{domain} not found (DNS may not be set up yet)"
            )
    except Exception as e:
        warn(f"SRV DNS check failed — {e}")


def test_journald_logs():
    """Verify journald is receiving MC logs."""
    import subprocess

    try:
        result = subprocess.run(
            [
                "ssh",
                SERVER,
                "journalctl -t e10-prod --since '1min ago' --no-pager 2>&1 | head -5",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.stdout.strip():
            ok("journald logs found for e10-prod")
        else:
            warn("No recent journald logs for e10-prod (server may have just started)")
    except Exception as e:
        warn(f"journald check failed — {e}")


# ── Main ──────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="E10 E2E Deployment Tests")
    parser.add_argument("--quick", action="store_true", help="Quick MOTD + ping only")
    parser.add_argument(
        "--instance", choices=["prod", "test"], help="Test only one instance"
    )
    args = parser.parse_args()

    instances = [args.instance] if args.instance else ["prod", "test"]
    quick = args.quick

    banner("E10 End-to-End Deployment Test")
    print(f"  Target: {SERVER}")
    print(f"  Instances: {', '.join(instances)}")
    print(f"  Mode: {'Quick' if quick else 'Full'}")
    print()

    # ── TCP connectivity ──
    banner("1. TCP Connectivity")
    for inst in instances:
        cfg = INSTANCES[inst]
        test_tcp_reachable(SERVER, cfg["port"], cfg["name"])

    # ── MC Status ──
    banner("2. Minecraft Server Status")
    for inst in instances:
        cfg = INSTANCES[inst]
        test_mc_status(SERVER, cfg["port"], cfg["name"])
        test_motd_format(SERVER, cfg["port"], cfg["name"])

    if quick:
        goto_summary()

    # ── Web-UI ──
    banner("3. Web-UI")
    test_webui_accessible()
    for inst in instances:
        test_webui_api(inst)

    # ── Grafana ──
    banner("4. Grafana")
    test_grafana_accessible()

    # ── DNS ──
    banner("5. DNS")
    for inst in instances:
        cfg = INSTANCES[inst]
        test_dns_srv(cfg["domain"])

    # ── Journald Logs ──
    banner("6. Journald Logs")
    test_journald_logs()

    goto_summary()


def goto_summary():
    banner("Summary")
    total = PASS + FAIL + WARN
    print(f"  ✅ {PASS} passed")
    print(f"  ❌ {FAIL} failed")
    print(f"  ⚠️  {WARN} warnings")
    print(f"  ─────────────")
    print(f"  📊 {total} total")

    if FAIL == 0 and WARN == 0:
        print("\n  🎉 ALL TESTS PASSED — E10 is ready for Yizzl!")
    elif FAIL == 0:
        print("\n  ⚠️  All critical tests passed (some warnings)")
    else:
        print(f"\n  ❌ {FAIL} TESTS FAILED — fixes needed before handover")
        sys.exit(1)


if __name__ == "__main__":
    main()
