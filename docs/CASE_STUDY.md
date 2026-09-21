# Case Study — python-utilities

**Repository:** [python-utilities](https://github.com/Freddricklogan/python-utilities) · **Package:** `pyutils-fl` (install from the repository with `uv tool` or `pipx`) · **Author:** Freddrick Logan

---

## 1. Who has this problem

Anyone who has written a few Python scripts for themselves — a task list, a note or post manager, a weather lookup — and now wants them to behave like software: installed once, validated, tested, and honest about what they do. Reviewers of a Python portfolio read these small repositories for fundamentals: structure, validation, persistence, and whether a "weather app" fetches weather.

## 2. The problem, as a scenario

A reviewer opens the repository and runs the weather script for her city. It prints a temperature. She runs it again and gets a different one; the code draws readings from `random.uniform` and the geocoder is labelled a mock. She tries the task list and adds a task with a blank title; it saves. She looks for tests and finds none. Each script has its own argument parser and writes a JSON file into whatever directory she happens to be in. That was the earlier version of this repository.

## 3. What it costs to leave it alone

A weather app that invents weather is a small lie in a portfolio, and small lies are what reviewers remember. Unvalidated records mean a data file that eventually cannot be loaded. Non-atomic writes mean a truncated file after an interruption. Three parsers for three scripts mean three copies of every bug and no single install. None of this is hard to fix, which is exactly why leaving it is costly.

## 4. The approach, and the alternative I rejected

I rejected consolidating the scripts into the fundamentals repository, which is for exercise-style analysis; these are tools, and tools should be installable. The three scripts became one package with a typer CLI. `store.py` reads and writes JSON atomically under one directory set by `PYUTILS_HOME`. `todo.py` and `blog.py` define Pydantic models for tasks, posts and comments and the operations on them — filtering with a stable priority order, overdue detection against a supplied date, unique slugs, word counts and reading time, search over titles, bodies and tags. `weather.py` calls Open-Meteo's geocoding and forecast APIs, which need no key, through an injected fetch function, maps WMO codes to words, and formats a report in Celsius or Fahrenheit. The CLI binds those modules and nothing else.

## 5. What the code does today

`pyutils todo add|list|done|rm` manages tasks with category, priority and due date, orders open tasks by priority then due date, marks overdue items, and prints statistics. `pyutils blog new|list|publish|comment|search` creates posts from a body file with a unique slug, tags, word count and reading time, toggles publication, records comments, and searches. `pyutils weather <place>` geocodes the place, fetches current conditions and a one-to-sixteen-day forecast, and prints them, with `--json` for scripts and `--fahrenheit` for readers who want it. Records are validated on creation and on load; every save is atomic; `PYUTILS_HOME` controls where data lives. CI installs the tool from the checkout with `uv tool` and runs it.

## 6. Evidence

Six tests at 99 % statement coverage cover the store's round trip, atomic write and rejection of non-list files; the task lifecycle — ids, title trimming, blank rejection, completion and double-completion, overdue logic, ordering, filters, statistics, persistence and removal; blog slugs including collisions and length caps, tag cleaning, word count and reading time, edits that are rejected without changing the post, publication, comments, search and statistics; and weather geocoding and forecast parsing on recorded responses with seven distinct rejections, null precipitation handling, unknown WMO codes, and Celsius and Fahrenheit formatting, plus the HTTP wrapper's error path. A live run for Chicago returned 16 °C, overcast, humidity 81 %, wind 28 km/h with a two-day forecast, and an unknown place raised a named error. `uv tool install` produced one executable. `AUDIT.md` records seven findings, including the edit-before-validate bug the tests caught in the first draft.

## 7. What it would take to run this in production

These are personal tools and need no server. To share them, publish to PyPI under the package name with a version tag; to sync across machines, point `PYUTILS_HOME` at a synchronised folder — the atomic writes make that safe enough for one user. The weather command already respects Open-Meteo's terms for non-commercial use; commercial use would need their paid tier.

## 8. Limits and next steps

Single-user JSON stores, no concurrency control beyond atomic replace; no registry publication yet; the blog manager renders nothing — it manages records. Next, in order: PyPI publication with a version workflow, a Markdown export for posts, and a `weather --hourly` view.

## 9. Who should look at this

**Hiring manager:** evidence that I finish small Python tools properly — validated, atomic, installable, tested — and replace a fake feature with a real one.
**Consulting client:** a clean example of packaging internal scripts into a maintained CLI.
**Engineer:** read `src/pyutils/blog.py` `edit` and its test for the validate-then-replace pattern, and `weather.py` for the injected-fetch design.
