"""Blog posts: slugs, word counts, reading time, search and comments, stored as JSON."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from .store import read_json, write_json

WORDS_PER_MINUTE = 200


def slugify(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:80] or "post"


class Comment(BaseModel):
    author: str = Field(min_length=1, max_length=80)
    body: str = Field(min_length=1, max_length=2000)
    at: datetime


class Post(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9-]{1,80}$")
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1)
    category: str = "general"
    tags: list[str] = Field(default_factory=list)
    created: datetime
    updated: datetime
    published: bool = False
    comments: list[Comment] = Field(default_factory=list)

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, v: list[str]) -> list[str]:
        return sorted({t.strip().lower() for t in v if t.strip()})

    @property
    def word_count(self) -> int:
        return len(self.body.split())

    @property
    def read_minutes(self) -> int:
        return max(1, -(-self.word_count // WORDS_PER_MINUTE))


class Blog:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.posts = [Post.model_validate(r) for r in read_json(path)]

    def save(self) -> None:
        write_json(self.path, [p.model_dump(mode="json") for p in self.posts])

    def _unique_slug(self, base: str) -> str:
        taken = {p.slug for p in self.posts}
        slug = base
        n = 2
        while slug in taken:
            slug = f"{base[:76]}-{n}"
            n += 1
        return slug

    def create(
        self,
        title: str,
        body: str,
        category: str = "general",
        tags: list[str] | None = None,
        now: datetime | None = None,
    ) -> Post:
        ts = now or datetime.now(UTC)
        post = Post(
            slug=self._unique_slug(slugify(title)),
            title=title,
            body=body,
            category=category,
            tags=tags or [],
            created=ts,
            updated=ts,
        )
        self.posts.append(post)
        return post

    def get(self, slug: str) -> Post:
        for p in self.posts:
            if p.slug == slug:
                return p
        msg = f"no post with slug {slug!r}"
        raise KeyError(msg)

    def edit(
        self,
        slug: str,
        title: str | None = None,
        body: str | None = None,
        now: datetime | None = None,
    ) -> Post:
        p = self.get(slug)
        update: dict[str, object] = {"updated": now or datetime.now(UTC)}
        if title is not None:
            update["title"] = title
        if body is not None:
            update["body"] = body
        # Validate the whole record before replacing it, so a bad edit leaves the post intact.
        edited = Post.model_validate({**p.model_dump(), **update})
        self.posts[self.posts.index(p)] = edited
        return edited

    def publish(self, slug: str, published: bool = True) -> Post:
        p = self.get(slug)
        p.published = published
        return p

    def comment(self, slug: str, author: str, body: str, now: datetime | None = None) -> Comment:
        p = self.get(slug)
        c = Comment(author=author, body=body, at=now or datetime.now(UTC))
        p.comments.append(c)
        return c

    def search(self, query: str, published_only: bool = False) -> list[Post]:
        q = query.lower().strip()
        return [
            p
            for p in self.posts
            if (not published_only or p.published)
            and (q in p.title.lower() or q in p.body.lower() or q in p.tags)
        ]

    def stats(self) -> dict[str, int]:
        return {
            "posts": len(self.posts),
            "published": sum(p.published for p in self.posts),
            "words": sum(p.word_count for p in self.posts),
            "comments": sum(len(p.comments) for p in self.posts),
        }
