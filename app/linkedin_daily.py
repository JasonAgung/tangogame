"""
Ambil puzzle Tango harian dari LinkedIn Games, ubah ke format data_puzzle,
lalu simpan ke data_puzzle/daily/.

Dijalankan berkala oleh systemd timer (lihat deploy/), bukan per request user:
    python -m app.linkedin_daily            # skip kalau puzzle hari ini sudah ada
    python -m app.linkedin_daily --force    # ambil ulang
    python -m app.linkedin_daily --from-file response.txt   # parse dari file (debug)

Env opsional:
    TANGO_BROWSER_CHANNEL=chrome   pakai Google Chrome terpasang (untuk dev lokal)
"""
import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .models import Puzzle, Constraint
from .solvers import BacktrackingSolver

GAME_URL = "https://www.linkedin.com/games/tango/"
PUZZLE_KEY = '"lotkaGamePuzzle":'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAILY_DIR = os.path.join(BASE_DIR, "data_puzzle", "daily")
LATEST_PATH = os.path.join(DAILY_DIR, "latest.json")

# puzzle LinkedIn ganti tiap tengah malam waktu Pacific
RESET_TZ = ZoneInfo("America/Los_Angeles")


def fetch_raw_response(timeout_s: int = 45) -> str:
    """Buka halaman game (tanpa login), klik Start, kembalikan body response yang berisi puzzle."""
    from playwright.sync_api import sync_playwright

    channel = os.environ.get("TANGO_BROWSER_CHANNEL") or None
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, channel=channel)
        try:
            context = browser.new_context(locale="en-US", viewport={"width": 1280, "height": 1000})
            page = context.new_page()

            responses = []
            page.on("response", lambda r: responses.append(r)
                    if "linkedin.com" in r.url and r.request.resource_type in ("document", "fetch", "xhr")
                    else None)

            page.goto(GAME_URL, wait_until="domcontentloaded", timeout=timeout_s * 1000)

            start_btn = page.locator("button, a").filter(has_text=re.compile(r"start game|play|mulai", re.I)).first
            try:
                start_btn.click(timeout=15000)
            except Exception:
                # tombol tidak ketemu (mungkin teks berubah), coba langsung ke layar game
                page.goto(GAME_URL + "?skipStartScreen=true", wait_until="domcontentloaded",
                          timeout=timeout_s * 1000)

            checked = 0
            deadline = timeout_s * 1000
            waited = 0
            while waited < deadline:
                while checked < len(responses):
                    resp = responses[checked]
                    checked += 1
                    try:
                        body = resp.text()
                    except Exception:
                        continue
                    if PUZZLE_KEY in body:
                        return body
                page.wait_for_timeout(500)
                waited += 500
        finally:
            browser.close()

    raise RuntimeError("Data puzzle tidak ditemukan di response LinkedIn (struktur halaman mungkin berubah)")


def parse_lotka(body: str) -> dict:
    """Ambil objek LotkaGamePuzzle (nama internal Tango di LinkedIn) dari body response."""
    idx = body.find(PUZZLE_KEY + "{")
    if idx < 0:
        raise ValueError("lotkaGamePuzzle tidak ada di response")
    raw, _ = json.JSONDecoder().raw_decode(body, idx + len(PUZZLE_KEY))

    edition = re.search(r'"todaysGameEditionText":"(\d+)"', body)
    difficulty = re.search(r'"Difficulty (\w+)"', body)
    return {
        "raw": raw,
        "edition": int(edition.group(1)) if edition else None,
        "difficulty": difficulty.group(1).lower() if difficulty else None,
    }


def to_app_format(parsed: dict) -> dict:
    """Konversi ke format yang sama dengan file di data_puzzle/<difficulty>/."""
    raw = parsed["raw"]
    size = raw["gridSize"]
    if size != 6:
        raise ValueError(f"gridSize {size} tidak didukung (solver hanya 6x6)")

    # LotkaCellValue_ZERO = Sun, LotkaCellValue_ONE = Moon
    solution = ["S" if v.endswith("ZERO") else "M" for v in raw["solution"]]
    if len(solution) != size * size:
        raise ValueError("Panjang solution tidak sesuai gridSize")

    grid = [[None] * size for _ in range(size)]
    givens = []
    for i in raw["presetCellIdxes"]:
        r, c = divmod(i, size)
        grid[r][c] = solution[i]
        givens.append([r, c])

    constraints = []
    for e in raw["edges"]:
        constraints.append({
            "cells": [list(divmod(e["startIdx"], size)), list(divmod(e["endIdx"], size))],
            "relationValue": "=" if e["isEqual"] else "x",
            "type": "relation",
        })

    return {
        "source": "linkedin",
        "edition": parsed["edition"],
        "difficulty": parsed["difficulty"],
        "grid": grid,
        "givens": givens,
        "constraints": constraints,
        "official_solution": [solution[r * size:(r + 1) * size] for r in range(size)],
    }


def solver_matches_official(puzzle: dict) -> bool:
    """Jalankan Backtracking kita dan bandingkan dengan kunci jawaban resmi."""
    p = Puzzle()
    full = {"S": "Sun", "M": "Moon", None: ""}
    p.grid = [[full[v] for v in row] for row in puzzle["grid"]]
    for c in puzzle["constraints"]:
        p.constraints.append(Constraint(c["type"], [tuple(x) for x in c["cells"]], c["relationValue"]))
    result = BacktrackingSolver(useHeuristic=True).solve(p)
    if result is None:
        return False
    short = {"Sun": "S", "Moon": "M"}
    return [[short[v] for v in row] for row in result.grid] == puzzle["official_solution"]


def _write_json_atomic(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def _reset_date(dt: datetime) -> str:
    return dt.astimezone(RESET_TZ).date().isoformat()


def already_fetched_today() -> bool:
    try:
        with open(LATEST_PATH) as f:
            latest = json.load(f)
        fetched = datetime.fromisoformat(latest["fetched_at"])
    except (OSError, KeyError, ValueError):
        return False
    return _reset_date(fetched) == _reset_date(datetime.now(timezone.utc))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true", help="ambil ulang walaupun puzzle hari ini sudah ada")
    ap.add_argument("--from-file", help="parse body response dari file, tanpa membuka browser")
    args = ap.parse_args(argv)

    if not args.force and not args.from_file and already_fetched_today():
        print("Puzzle hari ini sudah ada, skip.")
        return 0

    if args.from_file:
        with open(args.from_file, encoding="utf-8") as f:
            body = f.read()
    else:
        body = fetch_raw_response()

    puzzle = to_app_format(parse_lotka(body))
    puzzle["fetched_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    puzzle["date"] = _reset_date(datetime.now(timezone.utc))
    puzzle["solver_verified"] = solver_matches_official(puzzle)

    name = f"tango_{puzzle['edition']}.json" if puzzle["edition"] else f"tango_{puzzle['date']}.json"
    _write_json_atomic(os.path.join(DAILY_DIR, name), puzzle)
    _write_json_atomic(LATEST_PATH, puzzle)

    print(f"OK: Tango #{puzzle['edition']} ({puzzle['difficulty']}), "
          f"{len(puzzle['givens'])} givens, {len(puzzle['constraints'])} relasi, "
          f"solver cocok dengan kunci resmi: {puzzle['solver_verified']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
