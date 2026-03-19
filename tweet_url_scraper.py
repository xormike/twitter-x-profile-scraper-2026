#!/usr/bin/env python3
"""
tweet_url_scraper.py
====================
Scrapes tweet URLs from a X/Twitter profile using Chrome DevTools Protocol (CDP)
and xdotool for browser automation.

Requirements:
  - Linux with a running X11 desktop session
  - Google Chrome or Chromium installed
  - xdotool installed  (sudo apt install xdotool)
  - Python 3.10+
  - pip install websockets

Usage:
  python tweet_url_scraper.py --user elonmusk --since 2024-01-01 --until 2024-01-31
  python tweet_url_scraper.py --user elonmusk --since 2024-01-01 --until 2024-01-31 --output my_links.txt
  python tweet_url_scraper.py --user elonmusk --since 2024-01-01 --until 2024-01-31 --port 9223 --no-launch
"""

import asyncio
import urllib.request
import json as _json
import websockets
import re
import shutil
import subprocess
import sys
import time
import base64
import random
import argparse
from datetime import datetime, timedelta
from pathlib import Path


# ----------------- Defaults -----------------
DEFAULT_PORT         = 9222
DEFAULT_OUTPUT       = "tweet_urls.txt"
DEFAULT_SCROLL_CLICKS = 8
DEFAULT_SCROLL_WAIT  = 2.5
DEFAULT_IDLE_ROUNDS  = 4

CHROME_CANDIDATES = [
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
]


# ----------------- Dependency checks -----------------
def check_dependencies():
    errors = []

    if shutil.which("xdotool") is None:
        errors.append(
            "  ✗ xdotool nicht gefunden.\n"
            "    Installation: sudo apt install xdotool"
        )

    chrome_bin = find_chrome()
    if chrome_bin is None:
        errors.append(
            "  ✗ Kein Chrome/Chromium gefunden.\n"
            "    Installation: sudo apt install chromium-browser\n"
            "    Oder: https://www.google.com/chrome"
        )

    try:
        import websockets  # noqa: F401
    except ImportError:
        errors.append(
            "  ✗ Python-Paket 'websockets' fehlt.\n"
            "    Installation: pip install websockets"
        )

    if errors:
        print("❌ Fehlende Abhängigkeiten:\n")
        for e in errors:
            print(e)
        sys.exit(1)

    return chrome_bin


def find_chrome():
    for name in CHROME_CANDIDATES:
        path = shutil.which(name)
        if path:
            return path
    return None


# ----------------- Argument parsing -----------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Scrape tweet URLs from a X/Twitter profile by date range.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--user", "-u",
        required=True,
        help="X/Twitter screen name without @  (e.g. elonmusk)",
    )
    parser.add_argument(
        "--since", "-s",
        required=True,
        metavar="YYYY-MM-DD",
        help="Start date (inclusive)",
    )
    parser.add_argument(
        "--until", "-e",
        required=True,
        metavar="YYYY-MM-DD",
        help="End date (inclusive)",
    )
    parser.add_argument(
        "--output", "-o",
        default=DEFAULT_OUTPUT,
        metavar="FILE",
        help=f"Output file for tweet URLs (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=DEFAULT_PORT,
        help=f"Chrome remote debugging port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--no-launch",
        action="store_true",
        help="Do not launch Chrome automatically — use an already running instance",
    )
    parser.add_argument(
        "--scroll-clicks",
        type=int,
        default=DEFAULT_SCROLL_CLICKS,
        metavar="N",
        help=f"Mouse wheel clicks per scroll step (default: {DEFAULT_SCROLL_CLICKS})",
    )
    parser.add_argument(
        "--scroll-wait",
        type=float,
        default=DEFAULT_SCROLL_WAIT,
        metavar="SEC",
        help=f"Seconds to wait after each scroll for new responses (default: {DEFAULT_SCROLL_WAIT})",
    )
    parser.add_argument(
        "--idle-rounds",
        type=int,
        default=DEFAULT_IDLE_ROUNDS,
        metavar="N",
        help=f"Stop scrolling after N rounds with no new tweets (default: {DEFAULT_IDLE_ROUNDS})",
    )

    args = parser.parse_args()

    # Validate dates
    try:
        date_since = datetime.strptime(args.since, "%Y-%m-%d")
    except ValueError:
        parser.error(f"--since: ungültiges Datum '{args.since}' — Format muss YYYY-MM-DD sein.")

    try:
        date_until = datetime.strptime(args.until, "%Y-%m-%d")
    except ValueError:
        parser.error(f"--until: ungültiges Datum '{args.until}' — Format muss YYYY-MM-DD sein.")

    if date_since < date_until:
        parser.error(
            f"--since ({args.since}) muss gleich oder neuer als --until ({args.until}) sein.\n"
            "  Hinweis: --since ist der neuere Startpunkt, --until der ältere Endpunkt."
        )

    args.date_since = date_since
    args.date_until = date_until
    return args


# ----------------- Chrome launch -----------------
def launch_chrome(chrome_bin, port):
    """Launch Chrome with remote debugging enabled and return the process."""
    print(f"🚀 Starte Chrome ({chrome_bin}) mit --remote-debugging-port={port} ...")
    proc = subprocess.Popen(
        [
            chrome_bin,
            f"--remote-debugging-port={port}",
            "--no-first-run",
            "--no-default-browser-check",
            "https://x.com",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"   PID: {proc.pid} — warte auf CDP-Bereitschaft...")
    return proc


def wait_for_cdp(cdp_url, timeout=30):
    """Poll until CDP is reachable, return True on success."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{cdp_url}/json", timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


# ----------------- CDP helpers -----------------
def get_tab(cdp_url, url_fragment):
    try:
        tabs = _json.loads(urllib.request.urlopen(f"{cdp_url}/json").read())
        for tab in tabs:
            url = tab.get("url", "")
            ws  = tab.get("webSocketDebuggerUrl", "")
            if url_fragment in url and ws:
                return ws, url
    except Exception:
        pass
    return None, None


def get_chrome_window_id():
    """Try multiple xdotool queries to find the Chrome/Chromium window."""
    queries = [
        ["xdotool", "search", "--onlyvisible", "--name", "Google Chrome"],
        ["xdotool", "search", "--onlyvisible", "--name", "Chromium"],
        ["xdotool", "search", "--onlyvisible", "--class", "chrome"],
        ["xdotool", "search", "--onlyvisible", "--class", "chromium"],
        ["xdotool", "search", "--onlyvisible", "--class", "chromium-browser"],
    ]
    for q in queries:
        result = subprocess.run(q, capture_output=True, text=True)
        wids = result.stdout.strip().splitlines()
        if wids:
            return wids[0]  # erste gefundene Window-ID
    return None


def xdotool_scroll_down(window_id, clicks=8):
    subprocess.run(
        ["xdotool", "mousemove", "--window", window_id, "640", "400"],
        capture_output=True,
    )
    for _ in range(clicks):
        subprocess.run(
            ["xdotool", "click", "--clearmodifiers", "5"],
            capture_output=True,
        )


def navigate_to_url(win_id, url):
    subprocess.run(["xdotool", "windowactivate", "--sync", win_id], capture_output=True)
    subprocess.run(["xdotool", "key", "--window", win_id, "ctrl+l"], capture_output=True)
    time.sleep(0.5)
    subprocess.run(
        ["xdotool", "type", "--window", win_id, "--clearmodifiers", "--", url],
        capture_output=True,
    )
    time.sleep(0.3)
    subprocess.run(["xdotool", "key", "--window", win_id, "Return"], capture_output=True)


# ----------------- Data helpers -----------------
def snowflake_to_date(tid):
    try:
        ts = ((int(tid) >> 22) + 1288834974657) / 1000
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    except Exception:
        return "?"


def extract_ids_from_search(data):
    ids = []
    try:
        instructions = (data["data"]["search_by_raw_query"]
                           ["search_timeline"]["timeline"]["instructions"])
    except (KeyError, TypeError):
        return ids
    for instr in instructions:
        if instr.get("type") != "TimelineAddEntries":
            continue
        for entry in instr.get("entries", []):
            content = entry.get("content", {})
            if content.get("cursorType"):
                continue
            tweet = (content.get("itemContent", {})
                            .get("tweet_results", {})
                            .get("result", {}))
            tid = tweet.get("rest_id", "")
            if tid and len(tid) > 10:
                ids.append(tid)
    return ids


def append_urls(tweet_ids, all_file):
    known = set(all_file.read_text(encoding="utf-8").splitlines()) if all_file.exists() else set()
    new_urls = []
    with open(all_file, "a", encoding="utf-8") as f:
        for tid in tweet_ids:
            url = f"https://x.com/i/web/status/{tid}"
            if url not in known:
                f.write(url + "\n")
                known.add(url)
                new_urls.append(url)
    return new_urls


# ----------------- Main -----------------
async def main():
    args       = parse_args()
    chrome_bin = check_dependencies()
    cdp_url    = f"http://localhost:{args.port}"
    chrome_proc = None

    print(f"\n🐦 Tweet URL Scraper")
    print(f"   User:    @{args.user}")
    print(f"   Zeitraum: {args.until} → {args.since}")
    print(f"   Output:  {args.output}\n")

    # --- Chrome starten oder prüfen ob bereits läuft ---
    if args.no_launch:
        print(f"⏳ Prüfe CDP auf Port {args.port} ...")
        if not wait_for_cdp(cdp_url, timeout=5):
            print(
                f"❌ Kein Chrome mit CDP auf Port {args.port} gefunden.\n"
                f"   Starte Chrome manuell mit:\n"
                f"   {chrome_bin} --remote-debugging-port={args.port} https://x.com"
            )
            sys.exit(1)
    else:
        # Prüfen ob CDP schon läuft (z.B. vom letzten Aufruf)
        if wait_for_cdp(cdp_url, timeout=2):
            print(f"✅ Chrome mit CDP bereits aktiv auf Port {args.port}.")
        else:
            chrome_proc = launch_chrome(chrome_bin, args.port)
            if not wait_for_cdp(cdp_url, timeout=30):
                print("❌ Chrome gestartet, aber CDP antwortet nicht nach 30s.")
                chrome_proc.terminate()
                sys.exit(1)
            print(f"✅ Chrome bereit.")

    # --- Window-ID für xdotool ---
    print("🔍 Suche Chrome-Fenster für xdotool...")
    win_id = None
    for attempt in range(15):
        win_id = get_chrome_window_id()
        if win_id:
            break
        time.sleep(1)

    if not win_id:
        print(
            "❌ Chrome-Fenster nicht per xdotool gefunden.\n"
            "   Stelle sicher dass Chrome sichtbar auf dem Desktop läuft."
        )
        if chrome_proc:
            chrome_proc.terminate()
        sys.exit(1)
    print(f"🪟 Fenster gefunden (ID: {win_id})")

    # --- x.com Tab finden ---
    print("⏳ Suche x.com Tab in CDP...")
    ws_url = None
    for attempt in range(30):
        ws_url, tab_url = get_tab(cdp_url, "x.com")
        if ws_url:
            print(f"✅ Tab: {tab_url}")
            break
        await asyncio.sleep(1)

    if not ws_url:
        print(
            "❌ Kein x.com Tab gefunden.\n"
            "   Öffne x.com manuell in Chrome und starte das Skript erneut."
        )
        if chrome_proc:
            chrome_proc.terminate()
        sys.exit(1)

    # --- Bekannte URLs laden ---
    all_file = Path(args.output)
    seen_ids = set()
    if all_file.exists():
        for line in all_file.read_text(encoding="utf-8").splitlines():
            m = re.search(r'/status/(\d+)', line.strip())
            if m:
                seen_ids.add(m.group(1))
        print(f"📦 {len(seen_ids)} bereits bekannte URLs geladen aus {args.output}")

    # --- Tage-Liste aufbauen (neuestes zuerst) ---
    days = []
    current = args.date_since
    while current >= args.date_until:
        days.append(current)
        current -= timedelta(days=1)

    total_days  = len(days)
    total_found = 0

    print(f"📅 {total_days} Tage zu scrapen\n")

    # --- CDP WebSocket ---
    async with websockets.connect(ws_url, max_size=50 * 1024 * 1024) as ws:

        await ws.send(_json.dumps({"id": 1, "method": "Network.enable"}))
        await ws.recv()

        await ws.send(_json.dumps({
            "id": 2,
            "method": "Fetch.enable",
            "params": {
                "patterns": [
                    {"urlPattern": "*SearchTimeline*", "requestStage": "Response"},
                ]
            }
        }))
        await ws.recv()
        print(f"🎯 Fetch.enable aktiv\n")

        async def collect_responses(duration_sec):
            new_ids  = []
            deadline = asyncio.get_event_loop().time() + duration_sec
            pending  = {}

            while asyncio.get_event_loop().time() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=0.3)
                    msg = _json.loads(raw)

                    if msg.get("method") == "Fetch.requestPaused":
                        params     = msg["params"]
                        request_id = params["requestId"]
                        status     = params.get("responseStatusCode", 0)

                        if status == 200:
                            pending[request_id] = True
                            await ws.send(_json.dumps({
                                "id": 900,
                                "method": "Fetch.getResponseBody",
                                "params": {"requestId": request_id}
                            }))
                        else:
                            await ws.send(_json.dumps({
                                "id": 901,
                                "method": "Fetch.continueRequest",
                                "params": {"requestId": request_id}
                            }))

                    elif msg.get("id") == 900:
                        result   = msg.get("result", {})
                        body_str = result.get("body", "")
                        if result.get("base64Encoded"):
                            body_str = base64.b64decode(body_str).decode("utf-8")

                        if body_str:
                            try:
                                data = _json.loads(body_str)
                                ids  = extract_ids_from_search(data)
                                for tid in ids:
                                    if tid not in seen_ids:
                                        seen_ids.add(tid)
                                        new_ids.append(tid)
                                        print(f"   [+] {tid} ({snowflake_to_date(tid)})")
                            except Exception as e:
                                print(f"   [parse err] {type(e).__name__}: {e}")

                        if pending:
                            rid = next(iter(pending))
                            del pending[rid]
                            await ws.send(_json.dumps({
                                "id": 901,
                                "method": "Fetch.continueRequest",
                                "params": {"requestId": rid}
                            }))

                except asyncio.TimeoutError:
                    pass

            return new_ids

        for day_idx, day in enumerate(days):
            since = day.strftime("%Y-%m-%d")
            until = (day + timedelta(days=1)).strftime("%Y-%m-%d")

            print(f"[{day_idx+1}/{total_days}] 📅 {since}")

            search_url = (
                f"https://x.com/search?q=from%3A{args.user}"
                f"%20since%3A{since}%20until%3A{until}"
                f"%20-filter%3Areplies"
                f"&f=live&src=typed_query"
            )
            navigate_to_url(win_id, search_url)
            await asyncio.sleep(random.uniform(0.5, 1.5))

            subprocess.run(
                ["xdotool", "windowactivate", "--sync", win_id],
                capture_output=True,
            )

            day_ids      = []
            idle_rounds  = 0
            scroll_count = 0
            prev_count   = 0

            while True:
                xdotool_scroll_down(win_id, clicks=args.scroll_clicks)
                new_ids = await collect_responses(args.scroll_wait)
                day_ids.extend(new_ids)

                scroll_count += 1
                current_count = len(day_ids)

                if current_count == prev_count:
                    idle_rounds += 1
                    status = f"keine neuen ({idle_rounds}/{args.idle_rounds})"
                else:
                    idle_rounds = 0
                    status = f"+{current_count - prev_count} neue"

                print(f"   ⬇️  Scroll #{scroll_count:2d} | {status} | heute: {current_count}")
                prev_count = current_count

                if idle_rounds >= args.idle_rounds:
                    break

            if day_ids:
                saved = append_urls(day_ids, all_file)
                total_found += len(saved)
                print(f"   💾 {len(saved)} URLs gespeichert | gesamt: {total_found}")
            else:
                print(f"   — Keine Tweets gefunden")

        await ws.send(_json.dumps({"id": 3, "method": "Fetch.disable"}))

    print(f"\n✅ Fertig.")
    print(f"📊 {total_found} neue URLs über {total_days} Tage gefunden.")
    if all_file.exists():
        total_in_file = sum(1 for line in all_file.read_text().splitlines() if line.strip())
        print(f"📦 {args.output} enthält jetzt {total_in_file} URLs.")

    if chrome_proc:
        print("🔒 Chrome wird offen gelassen (manuell schließen).")


asyncio.run(main())
