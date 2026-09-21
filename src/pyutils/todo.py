"""Task list: validated records, filtering, completion and statistics."""

from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from .store import read_json, write_json


class Priority(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class Task(BaseModel):
    id: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=200)
    category: str = "personal"
    priority: Priority = Priority.medium
    due: date | None = None
    created: datetime
    completed: datetime | None = None

    @field_validator("title")
    @classmethod
    def strip(cls, v: str) -> str:
        if not v.strip():
            msg = "title must not be blank"
            raise ValueError(msg)
        return v.strip()

    @property
    def done(self) -> bool:
        return self.completed is not None

    def overdue(self, today: date) -> bool:
        return self.due is not None and not self.done and self.due < today


class TodoList:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.tasks = [Task.model_validate(r) for r in read_json(path)]

    def save(self) -> None:
        write_json(self.path, [t.model_dump(mode="json") for t in self.tasks])

    def add(
        self,
        title: str,
        category: str = "personal",
        priority: Priority = Priority.medium,
        due: date | None = None,
        now: datetime | None = None,
    ) -> Task:
        next_id = max((t.id for t in self.tasks), default=0) + 1
        task = Task(
            id=next_id,
            title=title,
            category=category,
            priority=priority,
            due=due,
            created=now or datetime.now(UTC),
        )
        self.tasks.append(task)
        return task

    def get(self, task_id: int) -> Task:
        for t in self.tasks:
            if t.id == task_id:
                return t
        msg = f"no task with id {task_id}"
        raise KeyError(msg)

    def complete(self, task_id: int, now: datetime | None = None) -> Task:
        t = self.get(task_id)
        if t.done:
            msg = f"task {task_id} is already complete"
            raise ValueError(msg)
        t.completed = now or datetime.now(UTC)
        return t

    def remove(self, task_id: int) -> None:
        t = self.get(task_id)
        self.tasks.remove(t)

    def filter(
        self,
        category: str | None = None,
        done: bool | None = None,
        priority: Priority | None = None,
    ) -> list[Task]:
        out = [
            t
            for t in self.tasks
            if (category is None or t.category == category)
            and (done is None or t.done == done)
            and (priority is None or t.priority == priority)
        ]
        order = {Priority.high: 0, Priority.medium: 1, Priority.low: 2}
        return sorted(out, key=lambda t: (t.done, order[t.priority], t.due or date.max, t.id))

    def stats(self, today: date) -> dict[str, int]:
        return {
            "total": len(self.tasks),
            "open": sum(not t.done for t in self.tasks),
            "done": sum(t.done for t in self.tasks),
            "overdue": sum(t.overdue(today) for t in self.tasks),
            "high": sum(t.priority == Priority.high and not t.done for t in self.tasks),
        }
