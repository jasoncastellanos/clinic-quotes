# clinic-quotes

Daily quote feed for the Castellanos Clinic morning digest (Power Automate Flow 2).

## How it works

```
GitHub Action (daily, 09:00 UTC)
        ↓ python3 scripts/pick.py
        ↓ commits today.json + corpus.json
        ↓
Power Automate Flow 2 (weekdays 06:30 ET)
        HTTP GET → today.json → injects quote into digest email
```

- `corpus.json` — vetted quote pool (~3000 entries, public domain).
  Each entry has tags (`themes`, `seasons`, `observances`, `tone`)
  and a `usedDate` field that the picker sets when the entry is consumed.
- `today.json` — single object (`{date, quote}`) that Power Automate fetches.
- `scripts/pick.py` — daily picker. Pure Python stdlib, deterministic, idempotent.
- `scripts/bootstrap.py` — one-shot generator. Re-run to refill from raw sources.
- `seed/quotes.json` — 53 hand-curated entries folded into corpus.json.
- `raw/bartlett-9th.txt` — Project Gutenberg #27889, Bartlett's *Familiar Quotations* 9th ed. (1905, public domain).

## Strict no-repeat invariant

`pick.py` only considers entries with `usedDate == null`. Once chosen, an
entry's `usedDate` is set to the pick date and is never reconsidered. At
~260 weekday picks per year and ~3000 entries, the pool lasts ~11 years
before refill is needed.

## Manual run

```
python3 scripts/pick.py
```

Idempotent — if `today.json` already has today's date, exits with no change.

## Power Automate fetch

Flow 2 should HTTP GET (cache-busted):

```
https://raw.githubusercontent.com/<USER>/clinic-quotes/main/today.json?t=<yyyyMMdd>
```

Parse JSON → use `body('Parse_JSON')?['quote']` in the email body Compose.

## Refill

When `usedDate == null` count gets low, `pick.py` prints a warning. To refill:

1. Edit/extend `scripts/bootstrap.py` to pull from another public-domain source.
2. Run it locally — it appends new entries with fresh ids.
3. Commit and push the new `corpus.json`.

## Sources

- Project Gutenberg eBook #27889 — *Familiar Quotations*, Compiled by John Bartlett, 9th ed. (Boston: Little, Brown, and Company, 1905). Public domain.
- 53 hand-curated entries from the original `clinic-task-tracker/quotes/quotes.json`.
