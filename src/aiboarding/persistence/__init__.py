"""Persistence layer for users, plans, and onboarding progress.

The public surface is the abstract `ProgressStore` (see `store.py`). SQLite is
the default backend; a future Firebase backend can implement the same interface
without touching callers.
"""

from aiboarding.persistence.store import (
    ProgressStore,
    SQLiteProgressStore,
    SQLProgressStore,
    StoredItem,
    StoredMessage,
    StoredPlan,
    StoredUser,
    get_progress_store,
)

__all__ = [
    "ProgressStore",
    "SQLiteProgressStore",
    "SQLProgressStore",
    "StoredItem",
    "StoredMessage",
    "StoredPlan",
    "StoredUser",
    "get_progress_store",
]
