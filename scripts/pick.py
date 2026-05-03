#!/usr/bin/env python3
"""
Daily picker. Pure stdlib, no external API.

- Loads corpus.json and today.json (if exists).
- If today.json already has today's date (UTC), exits 0 (idempotent).
- Otherwise picks an unused, include=true entry biased by date context
  (US/medical observance, season, weekday tone), marks it used, writes
  today.json, persists corpus.json.

Run from repo root:
    python3 scripts/pick.py
"""

from __future__ import annotations

import datetime as dt
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "corpus.json"
TODAY = REPO / "today.json"

# --------------------------------------------------------------------------
# Date context
# --------------------------------------------------------------------------

def season_for(d: dt.date) -> str:
    m = d.month
    if 3 <= m <= 5:   return "spring"
    if 6 <= m <= 8:   return "summer"
    if 9 <= m <= 11:  return "autumn"
    return "winter"


def nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> dt.date:
    """nth occurrence of `weekday` (0=Mon) in given month/year.
       n=-1 → last occurrence."""
    if n > 0:
        first = dt.date(year, month, 1)
        offset = (weekday - first.weekday()) % 7
        return first + dt.timedelta(days=offset + 7 * (n - 1))
    # last occurrence
    if month == 12:
        nxt = dt.date(year + 1, 1, 1)
    else:
        nxt = dt.date(year, month + 1, 1)
    last = nxt - dt.timedelta(days=1)
    offset = (last.weekday() - weekday) % 7
    return last - dt.timedelta(days=offset)


def observance_for(d: dt.date) -> str | None:
    """Return observance key if today is a recognized US/medical observance,
       within a small window around the actual date."""
    y, m, day = d.year, d.month, d.day
    fixed = {
        (1, 1):   "new-year",
        (3, 30):  "doctors-day",
        (5, 6):   "nurses-week",   # week 6–12 May; treat day 6 as anchor
        (5, 7):   "nurses-week",
        (5, 8):   "nurses-week",
        (5, 9):   "nurses-week",
        (5, 10):  "nurses-week",
        (5, 11):  "nurses-week",
        (5, 12):  "nurses-week",
        (7, 4):   "independence-day",
    }
    if (m, day) in fixed:
        return fixed[(m, day)]
    if d == nth_weekday_of_month(y, 5, weekday=6, n=2):
        return "mothers-day"
    if d == nth_weekday_of_month(y, 6, weekday=6, n=3):
        return "fathers-day"
    if d == nth_weekday_of_month(y, 5, weekday=0, n=-1):
        return "memorial-day"
    if d == nth_weekday_of_month(y, 9, weekday=0, n=1):
        return "labor-day"
    if d == nth_weekday_of_month(y, 11, weekday=3, n=4):
        return "thanksgiving"
    return None


WEEKDAY_TONE = {
    0: "uplifting",   # Monday — start of week
    1: "warm",        # Tuesday
    2: "wry",         # Wednesday — midweek levity
    3: "warm",        # Thursday
    4: "uplifting",   # Friday — close out strong
    5: "warm",        # Saturday
    6: "warm",        # Sunday
}


# --------------------------------------------------------------------------
# Picker
# --------------------------------------------------------------------------

def score(entry: dict, season: str, observance: str | None, tone_pref: str) -> int:
    s = 0
    if observance and observance in entry["observances"]:
        s += 3
    if season in entry["seasons"]:
        s += 2
    if entry["tone"] == tone_pref:
        s += 1
    return s


def main() -> int:
    today = dt.datetime.now(dt.timezone.utc).date()
    today_iso = today.isoformat()

    if TODAY.exists():
        existing = json.loads(TODAY.read_text())
        if existing.get("date") == today_iso:
            print(f"[skip] today.json already set for {today_iso}")
            return 0

    if not CORPUS.exists():
        print(f"[error] corpus missing: {CORPUS}", file=sys.stderr)
        return 1

    corpus = json.loads(CORPUS.read_text())
    eligible = [e for e in corpus if e["include"] and not e.get("usedDate")]
    if not eligible:
        print("[error] corpus exhausted — refill needed", file=sys.stderr)
        return 2
    if len(eligible) < 50:
        print(f"[warn] only {len(eligible)} unused entries remain — consider refill", file=sys.stderr)

    season = season_for(today)
    observance = observance_for(today)
    tone_pref = WEEKDAY_TONE[today.weekday()]
    print(f"[ctx] date={today_iso} season={season} observance={observance} tone_pref={tone_pref}")

    scored = [(score(e, season, observance, tone_pref), e) for e in eligible]
    max_score = max(s for s, _ in scored)
    # Take all entries at max score; if max==0, fall back to all eligible
    if max_score > 0:
        candidates = [e for s, e in scored if s == max_score]
    else:
        candidates = eligible
    print(f"[pick] eligible={len(eligible)} max_score={max_score} candidates_at_max={len(candidates)}")

    rng = random.Random(today_iso)
    chosen = rng.choice(candidates)

    # Mark chosen entry used
    for e in corpus:
        if e["id"] == chosen["id"]:
            e["usedDate"] = today_iso
            break

    formatted = format_quote(chosen)
    today_payload = {"date": today_iso, "quote": formatted}

    TODAY.write_text(json.dumps(today_payload, ensure_ascii=False, indent=2) + "\n")
    CORPUS.write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + "\n")

    print(f"[done] wrote {TODAY.name} (id={chosen['id']})")
    print(f"       {formatted}")
    return 0


def format_quote(e: dict) -> str:
    q = e["quote"].strip()
    parts = [q, "—", e["author"]]
    out = " ".join(parts)
    if e.get("source"):
        out = f"{out}, {e['source']}"
    return out


if __name__ == "__main__":
    sys.exit(main())
