import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request

app = Flask(__name__, template_folder="templates")

AUTH_USER = os.environ.get("AUTH_USER", "admin")
AUTH_PASS = os.environ.get("AUTH_PASS", "change-me")
RCON_HOST = os.environ.get("RCON_HOST_PROD", "mc-prod")
RCON_PORT = int(os.environ.get("RCON_PORT", 25575))
RCON_PASSWORD = os.environ["RCON_PASSWORD"]
ALLOWED_DIRS = {"config", "mods", "defaultconfigs", "world", "server.properties"}
KOFI_WEBHOOK_SECRET = os.environ.get("KOFI_WEBHOOK_SECRET", "")
TOTAL_FILE = "/data/donations_total.json"


def check_auth(username, password):
    return username == AUTH_USER and password == AUTH_PASS


def authenticate():
    return Response(
        "Authentication required",
        401,
        {"WWW-Authenticate": 'Basic realm="E10 Dashboard"'},
    )


def rcon(cmd, host=None):
    from mcrcon import MCRcon

    target = host or RCON_HOST
    try:
        with MCRcon(target, RCON_PASSWORD, port=RCON_PORT, timeout=5) as mcr:
            return mcr.command(cmd)
    except Exception as e:
        return f"RCON error: {e}"


def parse_list(resp):
    # Guard against RCON error messages
    if "RCON error" in resp or "Error" in resp:
        return []
    if ":" in resp:
        parts = resp.split(":", 1)
        if len(parts) > 1:
            return [p.strip() for p in parts[1].split(",") if p.strip()]
    return []


@app.before_request
def require_auth():
    if (
        request.path == "/"
        or request.path == "/metrics"
        or request.path.startswith("/api/prod/players")
        or request.path.startswith("/api/prod/motd")
        or request.path.startswith("/api/prod/whitelist/request")
        or request.path.startswith("/spenden")
        or request.path.startswith("/api/donations")
        or request.path.startswith("/api/kofi-webhook")
    ):
        return None
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()


@app.route("/")
def landing():
    return render_template("landing.html")


# --- Donations ---


def load_donations():
    try:
        with open(TOTAL_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"total_cents": 0, "count": 0, "goal_cents": 1500}


def save_donations(data):
    os.makedirs(os.path.dirname(TOTAL_FILE), exist_ok=True)
    with open(TOTAL_FILE, "w") as f:
        json.dump(data, f)


@app.get("/api/donations")
def api_donations():
    data = load_donations()
    total = data["total_cents"] / 100
    goal = data["goal_cents"] / 100
    return jsonify(
        {
            "total_eur": round(total, 2),
            "count": data["count"],
            "goal_eur": round(goal, 2),
            "progress_pct": min(
                100, round((data["total_cents"] / data["goal_cents"]) * 100)
            ),
        }
    )


@app.post("/api/kofi-webhook")
def api_kofi_webhook():
    # Ko-fi sends: { "data": "<urlencoded json string>" }
    if not KOFI_WEBHOOK_SECRET:
        return jsonify({"error": "webhook not configured"}), 501
    payload = json.loads(request.form.get("data", "{}"))
    if payload.get("verification_token") != KOFI_WEBHOOK_SECRET:
        return jsonify({"error": "forbidden"}), 403
    amount = float(payload.get("amount", 0))
    if amount <= 0:
        return jsonify({"error": "bad amount"}), 400
    data = load_donations()
    data["total_cents"] += int(amount * 100)
    data["count"] += 1
    save_donations(data)
    return jsonify({"status": "ok"})


@app.route("/spenden")
def spenden():
    return render_template("spenden.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/metrics")
def metrics():
    """Prometheus metrics endpoint for TPS, MSPT, players."""
    import re as _re

    instances = [
        ("prod", os.environ.get("RCON_HOST_PROD", "mc-prod")),
    ]
    lines = []
    for instance, host in instances:
        resp = rcon("tick query", host=host)
        tps, mspt, up = 0.0, 0.0, 0
        if resp and "time per tick" in resp:
            m = _re.search(r"time per tick:\s*([\d.]+)ms", resp)
            if m:
                mspt = float(m.group(1))
                tps = min(20.0, round(1000.0 / mspt, 1)) if mspt > 0 else 20.0
                up = 1
        lines.append(f'minecraft_tps{{instance="{instance}"}} {tps}')
        lines.append(f'minecraft_mspt_seconds{{instance="{instance}"}} {mspt / 1000.0}')
        headroom = max(0, (50.0 - mspt) / 50.0 * 100) if mspt > 0 else 100.0
        lines.append(
            f'minecraft_tick_headroom_percent{{instance="{instance}"}} {headroom:.1f}'
        )
        lines.append(f'minecraft_up{{instance="{instance}"}} {up}')
        resp = rcon("list", host=host)
        online, maxp = 0, 0
        if resp and "players online" in resp:
            m = _re.search(r"There are (\d+) of a max (?:of )?(\d+) player", resp)
            if m:
                online = int(m.group(1))
                maxp = int(m.group(2))
        lines.append(f'minecraft_players_online{{instance="{instance}"}} {online}')
        lines.append(f'minecraft_players_max{{instance="{instance}"}} {maxp}')
    header = (
        "# HELP minecraft_tps Current ticks per second (max 20)\n"
        "# TYPE minecraft_tps gauge\n"
        "# HELP minecraft_mspt_seconds Milliseconds per tick in seconds\n"
        "# TYPE minecraft_mspt_seconds gauge\n"
        "# HELP minecraft_tick_headroom_percent Percent of 50ms tick budget remaining\n"
        "# TYPE minecraft_tick_headroom_percent gauge\n"
        "# HELP minecraft_up 1 if Minecraft server is reachable via RCON\n"
        "# TYPE minecraft_up gauge\n"
        "# HELP minecraft_players_online Currently online players\n"
        "# TYPE minecraft_players_online gauge\n"
        "# HELP minecraft_players_max Maximum player slots\n"
        "# TYPE minecraft_players_max gauge\n"
    )
    return Response(header + "\n".join(lines) + "\n", mimetype="text/plain")


@app.route("/api/<instance>/players")
def api_players(instance):
    return jsonify(parse_list(rcon("list")))


@app.route("/api/<instance>/whitelist")
def api_whitelist(instance):
    resp = rcon("whitelist list")
    if "whitelisted" in resp:
        return jsonify(parse_list(resp))
    return jsonify([])


@app.route("/api/<instance>/whitelist/add", methods=["POST"])
def api_whitelist_add(instance):
    name = request.json.get("name", "")
    if not name:
        return jsonify({"error": "name required"}), 400
    return jsonify({"result": rcon(f"whitelist add {name}").strip()})


@app.route("/api/<instance>/whitelist/remove", methods=["POST"])
def api_whitelist_remove(instance):
    name = request.json.get("name", "")
    if not name:
        return jsonify({"error": "name required"}), 400
    return jsonify({"result": rcon(f"whitelist remove {name}").strip()})


@app.route("/api/<instance>/whitelist/request", methods=["POST"])
def api_whitelist_request(instance):
    name = request.json.get("name", "").strip()
    if not name or len(name) < 2 or len(name) > 16:
        return jsonify({"error": "Invalid name"}), 400
    req_file = Path("/prod-data/whitelist-requests.json")
    try:
        requests = json.loads(req_file.read_text()) if req_file.exists() else []
    except Exception:
        requests = []
    if any(r["name"].lower() == name.lower() for r in requests):
        return jsonify({"result": "Already requested"})
    requests.append({"name": name, "time": datetime.now().isoformat()})
    req_file.write_text(json.dumps(requests, indent=2))
    return jsonify({"result": f"Request submitted for {name}"})


@app.route("/api/<instance>/whitelist/requests")
def api_whitelist_requests(instance):
    req_file = Path("/prod-data/whitelist-requests.json")
    try:
        return jsonify(json.loads(req_file.read_text()) if req_file.exists() else [])
    except Exception:
        return jsonify([])


@app.route("/api/<instance>/whitelist/requests/approve", methods=["POST"])
def api_whitelist_requests_approve(instance):
    name = request.json.get("name", "")
    resp = rcon(f"whitelist add {name}")
    req_file = Path("/prod-data/whitelist-requests.json")
    if req_file.exists():
        try:
            requests = json.loads(req_file.read_text())
            requests = [r for r in requests if r["name"].lower() != name.lower()]
            req_file.write_text(json.dumps(requests, indent=2))
        except Exception:
            pass
    return jsonify({"result": resp.strip()})


@app.route("/api/<instance>/whitelist/requests/reject", methods=["POST"])
def api_whitelist_requests_reject(instance):
    name = request.json.get("name", "")
    req_file = Path("/prod-data/whitelist-requests.json")
    if req_file.exists():
        try:
            requests = json.loads(req_file.read_text())
            requests = [r for r in requests if r["name"].lower() != name.lower()]
            req_file.write_text(json.dumps(requests, indent=2))
        except Exception:
            pass
    return jsonify({"result": f"Rejected {name}"})


@app.route("/api/<instance>/cmd", methods=["POST"])
def api_cmd(instance):
    return jsonify({"result": rcon(request.json.get("cmd", "")).strip()})


@app.route("/api/<instance>/tps")
def api_tps(instance):
    # Use vanilla /tick query (works via RCON, unlike spark)
    resp = rcon("tick query")
    tps_val = "--"
    mspt_val = "--"
    if resp and "Average time per tick" in resp:
        import re as _re

        m = _re.search(r"Average time per tick:\s*([\d.]+)ms", resp)
        if m:
            mspt = float(m.group(1))
            mspt_val = f"{mspt:.1f}ms"
            tps = min(20.0, round(1000.0 / mspt, 1)) if mspt > 0 else 20.0
            tps_val = f"{tps:.1f}"
    return jsonify({"tps": tps_val, "mspt": mspt_val})


# Pre-gen: only pause when cage is released AND players online
cage_released = False


@app.route("/api/<instance>/pregen")
def api_pregen(instance):
    # Check actual worldborder to detect if cage was released (persistent across restarts)
    wb_resp = rcon("worldborder get")
    cage_open = "59999968" in wb_resp
    players = parse_list(rcon("list"))
    prog = rcon("chunky progress").strip()
    idle = "No tasks" in prog or "RCON error" in prog

    if idle:
        rcon("chunky world world")
        rcon("chunky radius 2000")
        rcon("chunky start")
        prog = "Starting..."
    elif cage_open and len(players) > 0:
        rcon("chunky pause")
        prog = "Paused (cage open, players online)"
    else:
        rcon("chunky continue")
        prog = rcon("chunky progress").strip()

    return jsonify(
        {"running": not idle, "progress": prog, "radius": 2000, "cage_open": cage_open}
    )


@app.route("/api/<instance>/cage/go", methods=["POST"])
def api_cage_go(instance):
    rcon("worldborder set 59999968")
    rcon("gamemode survival @a")
    rcon('title @a title {"text":"GO!","color":"green"}')
    rcon("say §a§lCage released! Welcome to Enigmatica 10!")
    return jsonify({"result": "Cage released"})


@app.route("/api/<instance>/motd")
def api_motd(instance):
    try:
        props = Path("/prod-data/server.properties")
        motd_raw = ""
        with open(props) as f:
            for line in f:
                if line.startswith("motd="):
                    motd_raw = line[5:].strip()
                    break
        # Strip leading backslash (server.properties escape)
        if motd_raw.startswith("\\ "):
            motd_raw = " " + motd_raw[2:]
        return jsonify({"raw": motd_raw})
    except Exception as e:
        return jsonify({"raw": f"Error: {e}"})


@app.route("/api/<instance>/motd", methods=["POST"])
def api_set_motd(instance):
    raw = request.json.get("raw", "")
    try:
        props = Path("/prod-data/server.properties")
        lines = open(props).readlines()
        motd_line = f"motd={raw}\n"
        found = False
        with open(props, "w") as f:
            for line in lines:
                if line.startswith("motd="):
                    f.write(motd_line)
                    found = True
                else:
                    f.write(line)
            if not found:
                f.write(motd_line)
        rcon("reload")
        rcon("say §6MOTD updated")
        return jsonify({"result": "MOTD updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def safe_path(rel_path):
    base = Path("/prod-data").resolve()
    target = (base / rel_path).resolve()
    if not str(target).startswith(str(base)):
        raise ValueError("Path traversal denied")
    return target


def file_info(p, base):
    rel = str(p.relative_to(base))
    stat = p.stat()
    return {
        "name": p.name,
        "path": rel,
        "dir": p.is_dir(),
        "size": _human_size(stat.st_size) if p.is_file() else "",
    }


def _human_size(n):
    for u in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.0f}{u}"
        n /= 1024
    return f"{n:.1f}TB"


@app.route("/api/<instance>/files")
def api_files(instance):
    rel = request.args.get("path", "")
    try:
        target = safe_path(rel) if rel else Path("/prod-data")
        if not target.exists():
            return jsonify([])
        items = []
        for entry in sorted(
            target.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())
        ):
            if entry.name.startswith("."):
                continue
            if (
                rel == ""
                and entry.name not in ALLOWED_DIRS
                and entry.name != "server.properties"
            ):
                if entry.is_dir():
                    continue
            items.append(file_info(entry, Path("/prod-data")))
        return jsonify(items)
    except ValueError as e:
        return jsonify({"error": str(e)}), 403


@app.route("/api/<instance>/files/read")
def api_files_read(instance):
    try:
        target = safe_path(request.args.get("path", ""))
        if not target.is_file():
            return jsonify({"error": "Not a file"}), 400
        return jsonify({"content": target.read_text(errors="replace")})
    except ValueError as e:
        return jsonify({"error": str(e)}), 403


@app.route("/api/<instance>/files/write", methods=["POST"])
def api_files_write(instance):
    d = request.json
    try:
        target = safe_path(d.get("path", ""))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(d.get("content", ""))
        return jsonify({"result": "Saved"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 403


@app.route("/api/<instance>/files/delete", methods=["POST"])
def api_files_delete(instance):
    try:
        target = safe_path(request.json.get("path", ""))
        shutil.rmtree(target) if target.is_dir() else target.unlink()
        return jsonify({"result": "Deleted"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 403


@app.route("/api/<instance>/files/rename", methods=["POST"])
def api_files_rename(instance):
    d = request.json
    try:
        target = safe_path(d.get("path", ""))
        target.rename(target.parent / d.get("new_name", ""))
        return jsonify({"result": "Renamed"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 403


@app.route("/api/<instance>/files/upload", methods=["POST"])
def api_files_upload(instance):
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file"}), 400
    try:
        rel = request.form.get("path", "")
        base = safe_path(rel) if rel else Path("/prod-data")
        target = base / f.filename
        if not str(target.resolve()).startswith(str(Path("/prod-data").resolve())):
            return jsonify({"error": "Path traversal"}), 403
        target.parent.mkdir(parents=True, exist_ok=True)
        f.save(str(target))
        return jsonify({"result": "Uploaded"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 403


@app.route("/api/<instance>/files/mkdir", methods=["POST"])
def api_files_mkdir(instance):
    try:
        safe_path(request.json.get("path", "")).mkdir(parents=True, exist_ok=True)
        return jsonify({"result": "Created"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 403


@app.route("/api/<instance>/logs")
def api_logs(instance):
    import docker

    tail = request.args.get("tail", 50, type=int)
    ansi_re = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\x1b\]0;.*?\x07|\r")
    try:
        client = docker.from_env()
        container = client.containers.get("mc-prod")
        # Fetch more lines to compensate for RCON filter
        logs = container.logs(tail=max(tail * 5, 500)).decode("utf-8", errors="replace")
        lines = []
        for l in logs.split("\n"):
            l = ansi_re.sub("", l).strip()
            if not l:
                continue
            # Filter RCON connect/disconnect noise
            if "[minecraft/RconClient]" in l or "[minecraft/GenericThread]" in l:
                continue
            # Strip progress bar prefix
            if l.startswith(">"):
                l = l.split("\r")[-1].lstrip(">. ")
            lines.append(l)
        return jsonify(lines[-tail:])
    except Exception as e:
        return jsonify([f"Error: {e}"]), 500


@app.route("/api/<instance>/backup", methods=["POST"])
def api_backup(instance):
    try:
        subprocess.run(
            ["borg", "init", "--encryption=none", "/prod-backups"],
            capture_output=True,
            timeout=15,
        )
        rcon("save-all")
        subprocess.run(["sleep", "3"], capture_output=True)
        subprocess.run(
            [
                "borg",
                "create",
                "--stats",
                "--compression",
                "lz4",
                f"/prod-backups::prod-{_now()}",
                "world",
            ],
            cwd="/prod-data",
            capture_output=True,
            text=True,
            timeout=300,
        )
        subprocess.run(
            [
                "borg",
                "prune",
                "--keep-hourly",
                "48",
                "--keep-daily",
                "30",
                "--keep-weekly",
                "12",
                "/prod-backups",
            ],
            capture_output=True,
            timeout=30,
        )
        return jsonify({"result": "Backup completed"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/<instance>/backups")
def api_backups(instance):
    try:
        result = subprocess.run(
            ["borg", "list", "--format", "{archive}{TAB}{start}", "/prod-backups"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        snapshots = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            snapshots.append(
                {"name": parts[0], "date": parts[1] if len(parts) > 1 else ""}
            )
        return jsonify(snapshots[-10:])
    except Exception:
        return jsonify([])


@app.route("/api/<instance>/restore", methods=["POST"])
def api_restore(instance):
    snapshot = request.json.get("snapshot", "")
    if not snapshot:
        return jsonify({"error": "snapshot required"}), 400
    try:
        rcon("stop")
        import socket
        import time

        for _ in range(30):
            time.sleep(2)
            try:
                s = socket.create_connection((RCON_HOST, 25565), timeout=2)
                s.close()
            except (ConnectionRefusedError, OSError):
                break
        time.sleep(5)
        subprocess.run(
            ["borg", "extract", f"/prod-backups::{snapshot}"],
            cwd="/prod-data",
            capture_output=True,
            text=True,
            timeout=120,
        )
        return jsonify({"result": f"Restored {snapshot}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _now():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
