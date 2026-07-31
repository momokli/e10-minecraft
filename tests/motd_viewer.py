#!/usr/bin/env python3
"""
Quick MOTD viewer — connects to MC server and shows the MOTD as players see it.

Usage:
  python tests/motd_viewer.py
  python tests/motd_viewer.py --port 25580  # TEST instance
"""

import argparse
import sys

from mcstatus import JavaServer

SERVER = "projectmellon.de"


def main():
    parser = argparse.ArgumentParser(description="View E10 MOTD as players see it")
    parser.add_argument(
        "--port", type=int, default=25585, help="Server port (25585=PROD, 25580=TEST)"
    )
    args = parser.parse_args()

    label = (
        "PROD"
        if args.port == 25585
        else "TEST"
        if args.port == 25580
        else str(args.port)
    )
    print(f"Connecting to {SERVER}:{args.port} ({label})...")

    try:
        server = JavaServer.lookup(f"{SERVER}:{args.port}")
        status = server.status()
        motd_plain = status.motd.to_plain()

        print()
        print("─" * 60)
        print("  MOTD (formatted — how players see it):")
        print("─" * 60)
        print(status.motd.to_minecraft())
        print("─" * 60)
        print(f"  Version:  {status.version.name}")
        print(f"  Players:  {status.players.online}/{status.players.max}")
        print(f"  Latency:  {status.latency:.0f}ms")
        print("─" * 60)

    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
