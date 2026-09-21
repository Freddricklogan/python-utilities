from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from pyutils.blog import Blog, slugify
from pyutils.store import read_json, write_json
from pyutils.todo import Priority, TodoList

NOW = datetime(2026, 9, 21, 12, 0, tzinfo=UTC)


def test_store_round_trip_and_rejection(tmp_path: Path) -> None:
    p = tmp_path / "a.json"
    assert read_json(p) == []
    write_json(p, [{"x": 1}])
    assert read_json(p) == [{"x": 1}]
    assert not p.with_suffix(".json.tmp").exists()
    p.write_text("{}")
    with pytest.raises(ValueError, match="JSON list"):
        read_json(p)


def test_todo_lifecycle_and_persistence(tmp_path: Path) -> None:
    path = tmp_path / "tasks.json"
    t = TodoList(path)
    a = t.add("Write report", "work", Priority.high, date(2026, 9, 20), now=NOW)
    b = t.add("  Buy milk ", now=NOW)
    c = t.add("Call bank", "finance", Priority.low, date(2026, 9, 30), now=NOW)
    assert (a.id, b.id, c.id) == (1, 2, 3)
    assert b.title == "Buy milk"
    with pytest.raises(ValueError, match="blank"):
        t.add("   ")
    t.complete(2, now=NOW)
    with pytest.raises(ValueError, match="already"):
        t.complete(2)
    with pytest.raises(KeyError):
        t.get(99)
    today = date(2026, 9, 21)
    assert a.overdue(today) and not c.overdue(today) and not b.overdue(today)
    assert [x.id for x in t.filter()] == [1, 3, 2]  # high first, then low by due, done last
    assert [x.id for x in t.filter(done=False)] == [1, 3]
    assert [x.id for x in t.filter(category="finance")] == [3]
    assert [x.id for x in t.filter(priority=Priority.high)] == [1]
    assert t.stats(today) == {"total": 3, "open": 2, "done": 1, "overdue": 1, "high": 1}
    t.save()
    again = TodoList(path)
    assert [x.id for x in again.tasks] == [1, 2, 3] and again.get(2).done
    again.remove(1)
    assert [x.id for x in again.tasks] == [2, 3]
    assert again.add("next").id == 4


def test_blog_slugs_posts_comments_search(tmp_path: Path) -> None:
    path = tmp_path / "posts.json"
    b = Blog(path)
    assert slugify("Hello, World! Again") == "hello-world-again"
    assert slugify("!!!") == "post"
    assert len(slugify("x" * 200)) == 80
    p = b.create("Hello World", "word " * 450, tags=["Python", " python", "Notes"], now=NOW)
    assert p.slug == "hello-world" and p.tags == ["notes", "python"]
    assert p.word_count == 450 and p.read_minutes == 3
    q = b.create("Hello World", "short body", now=NOW)
    assert q.slug == "hello-world-2" and q.read_minutes == 1
    with pytest.raises(KeyError):
        b.get("nope")
    b.edit("hello-world", title="Hello Again", now=NOW)
    assert b.get("hello-world").title == "Hello Again"
    with pytest.raises(ValueError):
        b.edit("hello-world", title="")
    assert b.get("hello-world").title == "Hello Again"  # a rejected edit changes nothing
    b.publish("hello-world")
    b.comment("hello-world", "Ana", "Nice post", now=NOW)
    with pytest.raises(ValueError):
        b.comment("hello-world", "", "x")
    assert [x.slug for x in b.search("again")] == ["hello-world"]
    assert [x.slug for x in b.search("python")] == ["hello-world"]
    assert [x.slug for x in b.search("hello", published_only=True)] == ["hello-world"]
    assert b.stats() == {"posts": 2, "published": 1, "words": 452, "comments": 1}
    b.save()
    again = Blog(path)
    assert again.get("hello-world").comments[0].author == "Ana"
