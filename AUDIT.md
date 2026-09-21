# AUDIT — python-utilities (pre-refactor)

Audit of the previous build: three standalone scripts — `todo_app.py`
(384 lines), `blog_manager.py` (613), `weather_app.py` (443) — each
with its own argparse, its own JSON handling and no tests, and a
README listing three "tools" one of which was not real.

---

## A. Honesty

### A1 — A weather app with no weather
`weather_app.py:105` "(mock implementation)" for geocoding and
`generate_mock_weather` at line 123: temperature, humidity, wind and
pressure from `random.uniform` and `random.choice`. The README
described a weather application. **Fix:** Open-Meteo's geocoding and
forecast APIs, which need no key; the HTTP call is injected so parsing
is tested on recorded responses, and a live run for Chicago is in the
README.

## B. Correctness

### B1 — Records validated nowhere
Tasks and posts were dataclasses filled from user input and JSON with
no checks; a blank title or a malformed date persisted. **Fix:**
Pydantic models with field rules; the blog's `edit` validates the
whole record before replacing it, so a rejected edit leaves the post
unchanged (a test pins this — the first draft mutated first).

### B2 — Non-atomic writes
`json.dump` straight into the data file; an interrupted write left a
truncated file. **Fix:** write to a temporary file and `replace`.

### B3 — Data files in the working directory
Each script wrote `tasks.json`, `blog_data/` or `weather_data.json`
wherever it was run. **Fix:** one base directory, `~/.pyutils` by
default, overridable with `PYUTILS_HOME`.

### B4 — Slugs could collide
`blog_manager.py:67` derived a slug from the title with no uniqueness.
**Fix:** `-2`, `-3` suffixes with a length cap; tested.

## C. Engineering

### C1 — Three CLIs, no package, no install path
**Fix:** one `pyutils` command (typer) with `todo`, `blog` and
`weather` groups, installable with `pipx`/`uv tool`; CI installs it
from the checkout and runs it.

### C2 — No tests, types or CI
**Fix:** 6 pytest tests at 99 % statement coverage covering the store,
the task lifecycle and ordering, blog slugs/edits/comments/search, and
weather parsing with seven rejections; ruff, mypy strict, bandit,
pip-audit, Trivy.
