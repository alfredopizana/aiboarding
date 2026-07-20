"""Tests for the SQLite progress store and team-based plan personalization."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from aiboarding.models import UserProfile
from aiboarding.persistence import SQLiteProgressStore, get_progress_store
from aiboarding.plans.generator import PlanGenerator


@pytest.fixture
def store(tmp_path):
    return get_progress_store("sqlite", tmp_path / "t.db")


@pytest.fixture
def generator():
    gen = PlanGenerator(MagicMock(), MagicMock(), MagicMock())
    gen.store.retrieve.return_value = []
    gen.people.match.return_value = []
    gen.people.buddies.return_value = []
    gen.llm.model = "fake"
    return gen


def test_get_progress_store_unknown_backend(tmp_path):
    with pytest.raises(ValueError):
        get_progress_store("mongo", tmp_path / "x.db")


def test_sqlite_backend_type(store):
    assert isinstance(store, SQLiteProgressStore)


def test_upsert_user_is_idempotent_by_email(store):
    a = store.upsert_user(UserProfile(name="Ada", role="", team="data"), "ada@x.dev")
    b = store.upsert_user(UserProfile(name="Ada L.", role="", team="data"), "ada@x.dev")
    assert a.id == b.id
    assert store.get_user("ada@x.dev").name == "Ada L."  # updated in place


def test_get_user_missing_returns_none(store):
    assert store.get_user("nobody@x.dev") is None


def test_save_and_progress_roundtrip(store, generator):
    user = store.upsert_user(UserProfile(name="Ada", role="security", team="security"), "a@x.dev")
    plan = generator.generate(UserProfile(name="Ada", role="security", team="security"))
    stored = store.save_plan(user.id, plan)
    assert stored.total > 0
    assert stored.done_count == 0

    store.set_item_done(stored.items[0].id, True)
    refreshed = store.get_active_plan(user.id)
    assert refreshed.done_count == 1
    assert 0 < refreshed.progress < 1

    store.set_item_done(stored.items[0].id, False)
    assert store.get_active_plan(user.id).done_count == 0


def test_regenerate_deactivates_old_plan(store, generator):
    user = store.upsert_user(UserProfile(name="Ada", role="data", team="data"), "a@x.dev")
    first = store.save_plan(user.id, generator.generate(UserProfile(name="Ada", team="data")))
    store.set_item_done(first.items[0].id, True)
    second = store.save_plan(user.id, generator.generate(UserProfile(name="Ada", team="data")))
    active = store.get_active_plan(user.id)
    assert active.id == second.id != first.id
    assert active.done_count == 0  # fresh plan, progress reset


@pytest.mark.parametrize(
    "team,role,expected",
    [
        ("security", "", "security"),
        ("data", "", "data"),
        ("devops", "", "devops"),
        ("qa", "", "qa"),
        ("platform", "", "engineer"),
        ("web", "", "engineer"),
        ("it", "", "default"),
        ("", "product", "product"),
        ("unknown-team", "unknown-role", "default"),
    ],
)
def test_role_resolution(generator, team, role, expected):
    assert generator._resolve_role_key(UserProfile(name="x", role=role, team=team)) == expected
