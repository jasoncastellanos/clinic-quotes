#!/usr/bin/env python3
"""
One-time bootstrap: parse Bartlett's Familiar Quotations (9th ed., 1905,
public domain via Project Gutenberg #27889), tag entries, filter, and emit
corpus.json.

Run from the repo root:
    python3 scripts/bootstrap.py

Inputs:
    raw/bartlett-9th.txt  (Project Gutenberg plain text)
    seed/quotes.json      (53 hand-curated entries from clinic-task-tracker)

Output:
    corpus.json
"""

from __future__ import annotations

import json
import random
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "raw" / "bartlett-9th.txt"
SEED = REPO / "seed" / "quotes.json"
OUT = REPO / "corpus.json"

CONTENT_START_LINE = 1057   # GEOFFREY CHAUCER. 1328-1400.
CONTENT_END_LINE = 63800    # safely past last foreign-author entry, before misc/index

# Author header: ALL CAPS NAME, period, optional dates with hyphen, period.
# Examples:
#   GEOFFREY CHAUCER. 1328-1400.
#   THOMAS À KEMPIS. 1380-1471.
#   BISHOP STILL (JOHN). 1543-1607.
#   A. M. TOPLADY. 1740-1778.
#   VON MÜNCH BELLINGHAUSEN. 1806-1871.
AUTHOR_RE = re.compile(
    r"^([A-Z][A-Z .,'À-ÿ()-]+?)\. +(\d{3,4})\s*-\s*(\d{0,4})\.?$"
)

# Source citation: wrapped in underscores, often ends with period
SOURCE_RE = re.compile(r"^_(.+?)_\.?$")

# Footnote callouts in quote text: [598-1], [2-3]
FOOTNOTE_REF_RE = re.compile(r"\s*\[\d+-\d+\]")

# Page-break markers, etc.
PAGE_MARKER_RE = re.compile(r"^\s*\* {3,}\* {3,}\*")


@dataclass
class Entry:
    id: str
    quote: str
    author: str
    source: str
    themes: list[str] = field(default_factory=list)
    seasons: list[str] = field(default_factory=list)
    observances: list[str] = field(default_factory=list)
    tone: str = "warm"
    include: bool = True
    usedDate: Optional[str] = None


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

def parse_bartlett(text: str) -> list[Entry]:
    lines = text.splitlines()
    entries: list[Entry] = []

    state = "SEEKING"
    author = ""
    dates = ""
    quote_buf: list[str] = []
    in_footnotes = False
    seq = 0

    for i, raw_line in enumerate(lines):
        # Restrict to content range
        if i < CONTENT_START_LINE - 1:
            continue
        if i >= CONTENT_END_LINE:
            break

        line = raw_line.rstrip()
        stripped = line.strip()

        m = AUTHOR_RE.match(stripped)
        if m:
            # New author header — discard any in-progress quote (no source)
            author_raw = m.group(1).strip()
            birth = m.group(2)
            death = m.group(3) or ""
            author = normalize_author(author_raw)
            dates = f"{birth}–{death}" if death else birth
            state = "IN_AUTHOR"
            quote_buf = []
            in_footnotes = False
            continue

        if stripped == "FOOTNOTES:":
            in_footnotes = True
            quote_buf = []
            continue

        if in_footnotes or state != "IN_AUTHOR":
            continue

        if not stripped:
            # blank line — preserve buffer
            continue

        if PAGE_MARKER_RE.match(line):
            quote_buf = []
            continue

        # Source line?
        sm = SOURCE_RE.match(stripped)
        if sm and quote_buf:
            source = sm.group(1).strip().rstrip(".").strip()
            quote_text = clean_quote(quote_buf)
            quote_buf = []
            if quote_text:
                seq += 1
                entries.append(Entry(
                    id=f"bartlett-9th-{seq:05d}",
                    quote=quote_text,
                    author=author,
                    source=source,
                ))
            continue

        # Indented line → quote line
        if line.startswith("    ") and not stripped.startswith("_"):
            quote_buf.append(stripped)
            continue

        # Anything else: drop pending buffer (some kind of paragraph noise)
        quote_buf = []

    return entries


def normalize_author(s: str) -> str:
    """Convert ALL CAPS to Title Case, fix common particles."""
    s = s.strip().rstrip(".")
    parts = s.split()
    out = []
    keep_lower = {"de", "von", "van", "der", "della", "du", "la", "le", "of", "and"}
    for i, p in enumerate(parts):
        # Roman numerals stay caps
        if re.fullmatch(r"[IVX]+\.?", p):
            out.append(p)
            continue
        # Initials like "A." stay caps
        if re.fullmatch(r"[A-Z]\.", p):
            out.append(p)
            continue
        low = p.lower()
        if low in keep_lower and i != 0:
            out.append(low)
            continue
        # Title-case but preserve internal apostrophe / accents
        out.append(low.capitalize())
    # Special-case "À" / accented letters preserved via capitalize quirks
    return " ".join(out)


def clean_quote(buf: list[str]) -> str:
    """Join multi-line quote buffer; strip footnote refs; tidy whitespace."""
    text = " ".join(buf).strip()
    text = FOOTNOTE_REF_RE.sub("", text)
    # Collapse internal whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Drop trailing comma/dash artifacts
    text = text.rstrip(",;: -—")
    return text


# --------------------------------------------------------------------------
# Tagging
# --------------------------------------------------------------------------

THEME_KEYWORDS = {
    "wisdom":      [r"\bwise\w*\b", r"\bwisdom\b", r"\bknowledge\b", r"\blearn\w*\b", r"\bphilosoph\w*\b", r"\bunderstand\w*\b", r"\btruth\b"],
    "perseverance":[r"\bpersever\w*\b", r"\bendure\b", r"\bsteadfast\b", r"\bpatien\w*\b", r"\bresolute\b"],
    "courage":     [r"\bcourage\b", r"\bbrave\b", r"\bvalor\b", r"\bdaring\b", r"\bbold\b"],
    "humor":       [r"\blaugh\w*\b", r"\bjest\b", r"\bmirth\b", r"\bmerry\b", r"\bsmile\b", r"\bwit\b"],
    "beauty":      [r"\bbeauty\b", r"\bbeautiful\b", r"\blovely\b", r"\bgrace\b", r"\bfair\b"],
    "friendship":  [r"\bfriend\w*\b", r"\bcompanion\b", r"\bfellowship\b"],
    "love":        [r"\blove\b", r"\bloved\b", r"\bbeloved\b", r"\bheart\b"],
    "work":        [r"\bwork\b", r"\blabor\b", r"\btoil\b", r"\bduty\b", r"\bcraft\b"],
    "time":        [r"\btime\b", r"\bhour\b", r"\bmoment\b"],
    "nature":      [r"\bsea\b", r"\bocean\b", r"\bmountain\b", r"\bsky\b", r"\bstar\w*\b", r"\bbird\w*\b", r"\btree\w*\b", r"\bflower\w*\b", r"\briver\b"],
    "hope":        [r"\bhope\w*\b", r"\baspir\w*\b", r"\bdream\w*\b"],
    "kindness":    [r"\bkind\w*\b", r"\bgentle\w*\b", r"\bmercy\b", r"\bcompassion\b"],
    "humility":    [r"\bhumble\b", r"\bhumility\b", r"\bmodest\b"],
    "freedom":     [r"\bfreedom\b", r"\bliberty\b", r"\bfree\b"],
}

SEASON_KEYWORDS = {
    "spring": [r"\bspring\b", r"\bblossom\w*\b", r"\bblooming\b", r"\bbud\w*\b", r"\bMay\b", r"\bApril\b"],
    "summer": [r"\bsummer\b", r"\bJune\b", r"\bJuly\b", r"\bAugust\b", r"\bsunshine\b"],
    "autumn": [r"\bautumn\b", r"\bharvest\b", r"\bOctober\b", r"\bNovember\b", r"\bSeptember\b", r"\bleaves fall\b"],
    "winter": [r"\bwinter\b", r"\bsnow\w*\b", r"\bDecember\b", r"\bJanuary\b", r"\bFebruary\b", r"\bfrost\b", r"\bice\b"],
}

OBSERVANCE_KEYWORDS = {
    "doctors-day":     [r"\bphysician\b", r"\bdoctor\b", r"\bmedicin\w*\b", r"\bhealing\b"],
    "nurses-week":     [r"\bnurse\b", r"\btending\b", r"\bcare\b"],
    "mothers-day":     [r"\bmother\b", r"\bmaternal\b"],
    "fathers-day":     [r"\bfather\b", r"\bpaternal\b"],
    "memorial-day":    [r"\bsacrifice\b", r"\bfallen\b", r"\bsoldier\b", r"\bvalor\b"],
    "independence-day":[r"\bliberty\b", r"\bfreedom\b", r"\bcountry\b", r"\bnation\b"],
    "labor-day":       [r"\blabor\b", r"\bworkers?\b", r"\btoil\b"],
    "thanksgiving":    [r"\bthanks\w*\b", r"\bgrateful\b", r"\bgratitude\b", r"\bblessing\w*\b"],
    "new-year":        [r"\bnew year\b", r"\bnew years\b"],
}

UPLIFTING = [r"\bjoy\w*\b", r"\bhope\w*\b", r"\btriumph\w*\b", r"\bsuccess\b", r"\bglory\b", r"\bcheer\w*\b"]
GRAVE = [r"\bdeath\b", r"\bdying\b", r"\bdied\b", r"\bgrave\b", r"\bsorrow\w*\b", r"\bweep\w*\b", r"\bgrief\b", r"\btomb\b", r"\bcorpse\b"]
WRY = [r"\birony\b", r"\bjest\b", r"\bsatire\b", r"\bfool\w*\b"]


def tag(entry: Entry) -> None:
    text = entry.quote.lower()
    entry.themes = matched_keys(text, THEME_KEYWORDS)
    entry.seasons = matched_keys(text, SEASON_KEYWORDS)
    entry.observances = matched_keys(text, OBSERVANCE_KEYWORDS)
    entry.tone = pick_tone(text)


def matched_keys(text: str, keyword_map: dict[str, list[str]]) -> list[str]:
    found = []
    for key, patterns in keyword_map.items():
        for p in patterns:
            if re.search(p, text, re.IGNORECASE):
                found.append(key)
                break
    return found


def pick_tone(text: str) -> str:
    up = sum(1 for p in UPLIFTING if re.search(p, text, re.IGNORECASE))
    gr = sum(1 for p in GRAVE if re.search(p, text, re.IGNORECASE))
    wr = sum(1 for p in WRY if re.search(p, text, re.IGNORECASE))
    if gr >= 2 and gr > up:
        return "grave"
    if up >= 1 and up >= gr:
        return "uplifting"
    if wr >= 1:
        return "wry"
    return "warm"


# --------------------------------------------------------------------------
# Filtering
# --------------------------------------------------------------------------

# Hard exclude on slurs / openly racist or sexist phrasings / pseudoscience /
# violence / heavy grim or funereal content unsuited to a clinic email.
BLOCKLIST_PATTERNS = [
    # slurs / dated ethnic terms
    r"\bnegro\w*\b", r"\bnigger\w*\b", r"\bsavage\w*\b",
    r"\bsquaw\b", r"\bredskin\w*\b", r"\bhottentot\w*\b",
    r"\bjewess\b", r"\boriental\w*\b", r"\bbarbarian\w*\b",
    # gendered pseudo-philosophy
    r"\bweaker sex\b", r"\bfair sex\b", r"\bweaker vessel\b",
    # ableist / dated medical
    r"\bhysteri\w*\b", r"\blunatic\w*\b", r"\blunacy\b", r"\bidiot\w*\b", r"\bfeebleminded\b",
    r"\bcripple\w*\b", r"\bdumb (?:man|woman)\b", r"\bimbecile\w*\b",
    # crude / dated insults
    r"\bbastard\b", r"\bharlot\b", r"\bwench\b", r"\bknave\b", r"\bvulgar\b", r"\bbrat\b",
    # violence
    r"\bbloody\b", r"\bdamned?\b", r"\bhell\b",
    r"\bsuicid\w*\b", r"\bmurder\w*\b", r"\bkill\w+\b", r"\bslay\b", r"\bslain\b",
    r"\bbattle\w*\b", r"\bwar\b", r"\bwarrior\w*\b", r"\bsword\w*\b", r"\bspear\w*\b",
    r"\bdagger\w*\b", r"\barrow\w*\b", r"\bbow\b", r"\bblood\w*\b", r"\bweapon\w*\b",
    r"\btorment\w*\b", r"\btorture\w*\b", r"\banguish\w*\b",
    # grim / funereal
    r"\bdie\b", r"\bdied\b", r"\bdying\b", r"\bdead\b", r"\bdeath\b", r"\bperish\w*\b",
    r"\bfuneral\b", r"\bcoffin\w*\b", r"\bgrave\b", r"\btomb\b", r"\bsepulchre\b", r"\bsepulcher\b",
    r"\bmourn\w*\b", r"\bdespair\b", r"\bwail\w*\b", r"\bmisery\b", r"\bdoom\w*\b",
    r"\bcorpse\w*\b", r"\bmortal\w*\b", r"\bgrief\w*\b",
    # excessive royalty/court language
    r"\bharem\b",
    # alcohol-heavy
    r"\bdrunkard\b", r"\binebriat\w*\b",
    # additional grim adjectives
    r"\bgory\b", r"\bdoleful\b", r"\bdire\b",
]
BLOCKLIST_RE = re.compile("|".join(BLOCKLIST_PATTERNS), re.IGNORECASE)

# Religious / theological language — secular clinic, keep it neutral.
# We exclude any deity references, prayer, scripture, soul-of-man, sin/virtue
# preaching, etc. Bartlett's 1905 is dense with these; most aren't team-edifying.
RELIGIOUS_PATTERNS = [
    r"\bChrist\b", r"\bJesus\b", r"\bSavi(?:our|or)\b",
    r"\bdevil\b", r"\bsatan\b", r"\bhellfire\b",
    r"\bpurgatory\b",
    r"\bGod\b", r"\bGod's\b", r"\bgods?\b", r"\bgoddess\b",
    r"\bLord\b", r"\bLord's\b",  # capitalized as deity (line-start caught too)
    r"\bheaven\w*\b", r"\bAlmighty\b", r"\bdivine\b", r"\bdivin\w*\b",
    r"\bscripture\w*\b", r"\bprayer\w*\b", r"\bpray\b", r"\bpraying\b",
    r"\bsacred\b", r"\bholy\b",
    r"\bsoul\w*\b", r"\bsin\w*\b", r"\bvirtuous\b",
    r"\beternal\b", r"\beternity\b",
    r"\bAlmighty\b", r"\bblesséd\b", r"\bblest\b", r"\bblessed\b",
    r"\bangel\w*\b", r"\bcherub\w*\b",
    r"\bChristian\w*\b", r"\bbiblical\b", r"\bgospel\w*\b",
]
RELIGIOUS_RE = re.compile("|".join(RELIGIOUS_PATTERNS), re.IGNORECASE)

# Archaic English markers — any presence excludes (modern readability bar)
ARCHAIC_HARD_RE = re.compile(
    r"\b(?:thou|thee|thy|thine|ye|doth|hath|hast|wilt|shalt|wouldst|canst|"
    r"saith|cometh|knoweth|whence|whither|wherefore|verily|forsooth|methinks|"
    r"prithee|nay|yea|yon|yonder|hither|hencewith|hither|sayeth|"
    r"min|writ|hath|smote|smitten|begat|beseech|beseecheth|behold|hark|lo)\b",
    re.IGNORECASE,
)
# Apostrophe-elision archaisms ('tis, 'twas, e'er, o'er, ne'er, etc.)
# Also captures "'T is" (split form), "do 't", "for 't", and dated hyphenations.
ARCHAIC_APOSTROPHE_RE = re.compile(
    r"(?:^|[^A-Za-z])'(?:tis|twas|twere|twixt|gainst|gins|midst|mongst|neath)\b|"
    r"\b(?:o'er|ne'er|e'er)\b|"
    r"\B'T\s+is\b|"           # "'T is"
    r"\b(?:do|for|by|on|in)\s+'t\b|"  # "do 't", "for 't"
    r"\bto-(?:day|morrow|night|night)\b",  # dated hyphenations
    re.IGNORECASE,
)
# Suffix-archaic words like "loveth", "speaketh"
ARCHAIC_SUFFIX_RE = re.compile(r"\b\w{4,}(?:eth)\b", re.IGNORECASE)
# Past-tense apostrophe elision: touch'd, mock'd, scorn'd, shar'd, etc.
ARCHAIC_PAST_RE = re.compile(r"\b\w{3,}'d\b", re.IGNORECASE)


def acceptable(entry: Entry) -> tuple[bool, str]:
    q = entry.quote
    words = q.split()
    n = len(words)

    # Length: 6–28 words — punchier reads better in an email banner
    if n < 6:
        return False, "too short"
    if n > 28:
        return False, "too long"

    # Character length sanity
    if len(q) < 30 or len(q) > 220:
        return False, "char length"

    # Hard blocks
    if BLOCKLIST_RE.search(q):
        return False, "blocklist"

    # Religious specificity
    if RELIGIOUS_RE.search(q):
        return False, "religious"

    # Archaic — any thee/thou/hath/etc. excludes
    if ARCHAIC_HARD_RE.search(q):
        return False, "archaic"

    # Apostrophe-elision archaisms ('tis, 'twas, e'er, o'er, ne'er)
    if ARCHAIC_APOSTROPHE_RE.search(q):
        return False, "archaic-apostrophe"

    # Archaic suffix (-eth)
    if ARCHAIC_SUFFIX_RE.search(q):
        return False, "archaic-suffix"

    # Past-tense apostrophe elisions (touch'd, mock'd, etc.)
    if ARCHAIC_PAST_RE.search(q):
        return False, "archaic-past"

    # Fragment detection — first letter after opening quote must be uppercase
    inner = q.lstrip('"').lstrip("'").lstrip()
    if inner and inner[0].islower():
        return False, "fragment-lowercase-start"

    # Mid-sentence start (begins with conjunction-only fragment)
    first_word = inner.split()[0].rstrip(",.;:!?\"'").lower() if inner else ""
    if first_word in {"and", "but", "or", "nor", "yet", "so", "for"}:
        # only reject if no proper subject follows in first 3 words
        head = " ".join(inner.split()[:3]).lower()
        if not re.search(r"\b(i|we|you|he|she|it|they|all|none|every|any|the|a|this|that|these|those|when|where|why|how|what)\b", head):
            return False, "fragment-conjunction-start"

    # Must contain at least one ASCII letter
    if not re.search(r"[A-Za-z]", q):
        return False, "non-ascii"

    # Must end with letter, period, ! or ?
    last_char = q.rstrip()[-1]
    if last_char not in ".!?\"'":
        return False, "punct"

    # Skip foreign-language quotes (rough heuristic: look for non-ASCII
    # Latin clusters typical of French/German/Latin)
    foreign_ratio = sum(1 for c in q if ord(c) > 127) / max(len(q), 1)
    if foreign_ratio > 0.04:
        return False, "foreign"

    # Heuristic: must contain at least one common English word
    common = {"the", "and", "is", "a", "to", "of", "in", "that", "with", "for", "as", "but", "by", "be", "at", "we", "he", "she", "it", "I", "from", "on", "are", "was", "were", "have", "has", "do", "does", "no", "not", "all", "this", "they", "you", "your", "our", "his", "her", "their", "who", "what", "when", "where", "how", "why"}
    lower_words = {w.strip(",.;:!?\"'()").lower() for w in words}
    if not (lower_words & common):
        return False, "no-common-english"

    return True, "ok"


# --------------------------------------------------------------------------
# Seed entries (existing 53 hand-curated)
# --------------------------------------------------------------------------

def load_seeds() -> list[Entry]:
    if not SEED.exists():
        print(f"[warn] seed file missing: {SEED}", file=sys.stderr)
        return []
    raw = json.loads(SEED.read_text())
    out: list[Entry] = []
    seed_re = re.compile(r'^"(.+?)"\s*—\s*(.+?)(?:,\s*(.+))?$')
    for i, line in enumerate(raw, start=1):
        m = seed_re.match(line.strip())
        if not m:
            continue
        quote = '"' + m.group(1) + '"'
        author = m.group(2).strip()
        source = (m.group(3) or "").strip()
        e = Entry(
            id=f"seed-{i:03d}",
            quote=quote,
            author=author,
            source=source,
            tone="uplifting",
            include=True,
        )
        tag(e)
        # Override tone if seed had no obvious uplifting markers — they're all curated
        if e.tone == "warm":
            e.tone = "uplifting"
        out.append(e)
    return out


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> int:
    if not RAW.exists():
        print(f"[error] raw file missing: {RAW}", file=sys.stderr)
        return 1

    print(f"[info] reading {RAW}")
    text = RAW.read_text(encoding="utf-8")

    print("[info] parsing Bartlett's…")
    raw_entries = parse_bartlett(text)
    print(f"[info] parsed {len(raw_entries)} raw entries")

    print("[info] tagging + filtering…")
    accepted: list[Entry] = []
    reasons: dict[str, int] = {}
    for e in raw_entries:
        # Format quote with leading/trailing quotation marks for display
        e.quote = '"' + e.quote.strip('"').strip() + '"'
        tag(e)
        ok, reason = acceptable(e)
        if not ok:
            e.include = False
            reasons[reason] = reasons.get(reason, 0) + 1
            continue
        accepted.append(e)

    print(f"[info] {len(accepted)} accepted from Bartlett's")
    print(f"[info] rejection reasons: {sorted(reasons.items(), key=lambda x: -x[1])}")

    print("[info] loading seeds…")
    seeds = load_seeds()
    print(f"[info] {len(seeds)} seed entries")

    all_entries = seeds + accepted

    # Format: convert Entry objects to dicts in stable order
    out = [asdict(e) for e in all_entries]

    print(f"[info] writing {len(out)} entries to {OUT}")
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")

    # Show 10 random samples for spot-checking
    print("\n[samples — 10 random]")
    rng = random.Random(42)
    for e in rng.sample(out, k=min(10, len(out))):
        print(f"  [{e['tone']:9}] {e['quote']} — {e['author']}, {e['source']}")
        if e['themes'] or e['seasons'] or e['observances']:
            print(f"             themes={e['themes']} seasons={e['seasons']} obs={e['observances']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
