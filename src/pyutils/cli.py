"""Command-line entry point: `pyutils todo|blog|weather ...`."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import typer

from . import blog as blog_mod
from . import weather as weather_mod
from .store import default_dir
from .todo import Priority, TodoList

app = typer.Typer(add_completion=False, help="Task list, blog manager and weather lookup.")
todo_app = typer.Typer(help="Task list.")
blog_app = typer.Typer(help="Blog posts.")
app.add_typer(todo_app, name="todo")
app.add_typer(blog_app, name="blog")


@app.callback()
def main() -> None:
    """Task list, blog manager and weather lookup."""


def _todo() -> TodoList:
    return TodoList(default_dir() / "tasks.json")


def _blog() -> blog_mod.Blog:
    return blog_mod.Blog(default_dir() / "posts.json")


@todo_app.command("add")
def todo_add(
    title: str,
    category: str = typer.Option("personal", "--category", "-c"),
    priority: Priority = typer.Option(Priority.medium, "--priority", "-p"),
    due: str | None = typer.Option(None, help="YYYY-MM-DD"),
) -> None:
    """Add a task."""
    t = _todo()
    task = t.add(title, category, priority, date.fromisoformat(due) if due else None)
    t.save()
    print(f"added #{task.id}: {task.title}")


@todo_app.command("list")
def todo_list(
    category: str | None = typer.Option(None, "--category", "-c"),
    all_tasks: bool = typer.Option(False, "--all", help="include completed tasks"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """List open tasks (or all)."""
    t = _todo()
    rows = t.filter(category=category, done=None if all_tasks else False)
    if as_json:
        print(json.dumps([r.model_dump(mode="json") for r in rows], indent=1))
        return
    today = datetime.now(UTC).date()
    for r in rows:
        flag = "x" if r.done else ("!" if r.overdue(today) else " ")
        due = f" due {r.due.isoformat()}" if r.due else ""
        print(f"[{flag}] #{r.id} ({r.priority}, {r.category}) {r.title}{due}")
    s = t.stats(today)
    print(f"{s['open']} open, {s['done']} done, {s['overdue']} overdue, {s['high']} high priority")


@todo_app.command("done")
def todo_done(task_id: int) -> None:
    """Mark a task complete."""
    t = _todo()
    task = t.complete(task_id)
    t.save()
    print(f"completed #{task.id}")


@todo_app.command("rm")
def todo_rm(task_id: int) -> None:
    """Delete a task."""
    t = _todo()
    t.remove(task_id)
    t.save()
    print(f"removed #{task_id}")


@blog_app.command("new")
def blog_new(
    title: str,
    body_file: Path = typer.Option(..., "--body", help="file with the post body"),
    category: str = typer.Option("general", "--category", "-c"),
    tag: list[str] = typer.Option([], "--tag", "-t"),
) -> None:
    """Create a post from a body file."""
    b = _blog()
    post = b.create(title, body_file.read_text(encoding="utf-8"), category, tag)
    b.save()
    print(f"created {post.slug} ({post.word_count} words, {post.read_minutes} min read)")


@blog_app.command("list")
def blog_list(published: bool = typer.Option(False, "--published", help="published only")) -> None:
    """List posts."""
    for p in _blog().posts:
        if published and not p.published:
            continue
        state = "published" if p.published else "draft"
        print(
            f"{p.slug:40} {state:9} {p.word_count:5} words {len(p.comments):3} comments  {p.title}"
        )


@blog_app.command("publish")
def blog_publish(slug: str, unpublish: bool = typer.Option(False, "--unpublish")) -> None:
    """Publish (or unpublish) a post."""
    b = _blog()
    p = b.publish(slug, not unpublish)
    b.save()
    print(f"{p.slug}: {'published' if p.published else 'draft'}")


@blog_app.command("comment")
def blog_comment(slug: str, author: str, body: str) -> None:
    """Add a comment to a post."""
    b = _blog()
    b.comment(slug, author, body)
    b.save()
    print(f"comment added to {slug}")


@blog_app.command("search")
def blog_search(query: str) -> None:
    """Search titles, bodies and tags."""
    for p in _blog().search(query):
        print(f"{p.slug}: {p.title}")


@app.command()
def weather(
    place: str,
    days: int = typer.Option(3, "--days", "-d", min=1, max=16),
    fahrenheit: bool = typer.Option(False, "--fahrenheit", "-f"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Current conditions and a daily forecast from Open-Meteo (no API key)."""
    loc = weather_mod.geocode(place)
    r = weather_mod.forecast(loc, days)
    if as_json:
        print(
            json.dumps(
                {
                    "place": loc.__dict__,
                    "time": r.time,
                    "temperature_c": r.temperature_c,
                    "humidity_pct": r.humidity_pct,
                    "wind_kmh": r.wind_kmh,
                    "condition": r.condition,
                    "days": [d.__dict__ for d in r.days],
                },
                indent=1,
            )
        )
    else:
        print(weather_mod.format_report(r, fahrenheit))


if __name__ == "__main__":
    app()
