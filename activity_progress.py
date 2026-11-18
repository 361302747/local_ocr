"""Host-local activity statistics mounted by the OCR application."""

import argparse
from contextlib import closing
from datetime import date, datetime
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


def database_path():
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData/Local").resolve()
    if str(base).startswith("\\\\"):
        raise OSError("Activity progress database requires a local drive")
    if os.name == "nt":
        import ctypes
        if ctypes.windll.kernel32.GetDriveTypeW(base.anchor) == 4:
            raise OSError("Activity progress database cannot use a mapped network drive")
    return base / "GhostCatcher" / "activity_progress.sqlite3"


Name = Annotated[str, Field(min_length=1, max_length=160)]


class Event(BaseModel):
    event_id: UUID
    kind: Literal["increment", "timing"]
    day: date
    activity: Name
    owner: Name
    aliases: list[Name] = Field(default_factory=list, max_length=32)
    amount: int = Field(default=1, ge=1, le=100000)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    status: Literal["running", "completed", "stopped", "failed", "error"] = "running"
    daily_limit_reached: bool = False


class ProgressDatabase:
    def __init__(self, path):
        self.path = path

    def connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.path, timeout=2)

    def initialize(self, payload):
        """Import one authoritative snapshot; never merge it into live counts."""
        with closing(self.connect()) as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS initialized (id INTEGER PRIMARY KEY CHECK (id = 1));
                CREATE TABLE IF NOT EXISTS counts (
                    day TEXT, activity TEXT, owner TEXT, count INTEGER NOT NULL,
                    PRIMARY KEY (day, activity, owner)
                );
                CREATE TABLE IF NOT EXISTS timings (
                    day TEXT, owner TEXT, started TEXT NOT NULL, finished TEXT,
                    status TEXT NOT NULL, PRIMARY KEY (day, owner)
                );
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY, digest TEXT NOT NULL, result TEXT NOT NULL
                );
            """)
            with db:
                db.execute("BEGIN IMMEDIATE")
                if db.execute("SELECT 1 FROM initialized").fetchone():
                    return False
                for day, activities in payload.get("dates", {}).items():
                    day = date.fromisoformat(day).isoformat()
                    for activity, owners in activities.items():
                        for owner, count in owners.items():
                            db.execute("INSERT INTO counts VALUES (?, ?, ?, ?)",
                                       (day, activity, owner, max(0, int(count))))
                timings = {}
                for entries in payload.get("shimen_timing_history", {}).values():
                    for owner, record in entries.items():
                        timings[owner, datetime.fromisoformat(record["started_at"]).date()] = record
                for owner, record in payload.get("shimen_timings", {}).items():
                    timings[owner, datetime.fromisoformat(record["started_at"]).date()] = record
                for (owner, day), record in timings.items():
                    db.execute("INSERT INTO timings VALUES (?, ?, ?, ?, ?)", (
                        day.isoformat(), owner, record["started_at"], record.get("finished_at"), record["status"],
                    ))
                db.execute("INSERT INTO initialized VALUES (1)")
        return True

    def _require_initialized(self, db):
        has_table = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'initialized'"
        ).fetchone()
        if not has_table or not db.execute("SELECT 1 FROM initialized").fetchone():
            raise HTTPException(503, "Activity progress database not initialized")

    def snapshot(self, first, last):
        dates, timings = {}, {}
        with closing(self.connect()) as db, db:
            db.execute("BEGIN")
            self._require_initialized(db)
            for day, activity, owner, count in db.execute(
                "SELECT day, activity, owner, count FROM counts WHERE day BETWEEN ? AND ?", (first, last)
            ):
                dates.setdefault(day, {}).setdefault(activity, {})[owner] = count
            for day, owner, started, finished, status in db.execute(
                "SELECT day, owner, started, finished, status FROM timings WHERE day BETWEEN ? AND ?", (first, last)
            ):
                elapsed = (datetime.fromisoformat(finished) - datetime.fromisoformat(started)).total_seconds() if finished else 0
                timings.setdefault(day, {})[owner] = {
                    "started_at": started, "finished_at": finished, "status": status,
                    "elapsed_seconds": max(0, int(elapsed)),
                }
        return {"dates": dates, "shimen_timing_history": timings, "shimen_timings": timings.get(last, {})}

    def apply(self, event):
        event_id = str(event.event_id)
        digest = hashlib.sha256(event.model_dump_json().encode()).hexdigest()
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            self._require_initialized(db)
            prior = db.execute("SELECT digest, result FROM events WHERE id = ?", (event_id,)).fetchone()
            if prior:
                if prior[0] != digest:
                    raise HTTPException(409, "Event ID already used for a different completion")
                return {**json.loads(prior[1]), "event_id": event_id}
            if event.kind == "increment":
                result = {"count": self._update_count(db, event, event.day, event.amount)}
            else:
                result = self._apply_timing(db, event)
            db.execute("INSERT INTO events VALUES (?, ?, ?)", (event_id, digest, json.dumps(result)))
        return {**result, "event_id": event_id}

    @staticmethod
    def _update_count(db, event, day, amount, minimum=0):
        owner_keys = list(dict.fromkeys([event.owner, *event.aliases]))
        where = f"day = ? AND activity = ? AND owner IN ({','.join('?' for _ in owner_keys)})"
        params = (day.isoformat(), event.activity, *owner_keys)
        count = db.execute(f"SELECT COALESCE(SUM(count), 0) FROM counts WHERE {where}", params).fetchone()[0]
        count = max(minimum, count + amount)
        db.execute(f"DELETE FROM counts WHERE {where}", params)
        db.execute("INSERT INTO counts VALUES (?, ?, ?, ?)", (params[0], event.activity, event.owner, count))
        return count

    def _apply_timing(self, db, event):
        started, finished = event.started_at, event.finished_at
        if (event.activity != "shimen" or started is None or started.date() != event.day
                or started.tzinfo is not None or (finished and (finished.tzinfo is not None or finished < started))):
            raise HTTPException(422, "Invalid shimen timing")
        day = event.day.isoformat()
        started_iso = started.isoformat(timespec="seconds")
        finished_iso = finished.isoformat(timespec="seconds") if finished else None
        status = event.status
        previous = db.execute(
            "SELECT started, finished, status FROM timings WHERE day = ? AND owner = ?", (day, event.owner)
        ).fetchone()
        if previous:
            previous_completed = previous[2] == "completed"
            if (previous_completed and status != "completed"
                    or previous[1] and (previous[1], previous[2] != "running") > (finished_iso or started_iso, False)):
                finished_iso, status = previous[1:]
            started_iso = min(started_iso, previous[0])
        db.execute("INSERT OR REPLACE INTO timings VALUES (?, ?, ?, ?, ?)",
                   (day, event.owner, started_iso, finished_iso, status))
        if event.daily_limit_reached and event.status == "completed" and finished:
            self._update_count(db, event, finished.date(), 0, minimum=20)
        return {"started_at": started_iso}


router = APIRouter(prefix="/v1/activity-progress")


@router.get("/snapshot")
def read_snapshot(first: date, last: date):
    if not 0 <= (last - first).days <= 6:
        raise HTTPException(422, "Invalid activity snapshot date range")
    try:
        return ProgressDatabase(database_path()).snapshot(first.isoformat(), last.isoformat())
    except (OSError, sqlite3.Error):
        raise HTTPException(503, "Activity progress database unavailable") from None


@router.post("/events")
def record_event(event: Event):
    try:
        return ProgressDatabase(database_path()).apply(event)
    except (OSError, sqlite3.Error):
        raise HTTPException(503, "Activity progress database unavailable") from None


def main():
    parser = argparse.ArgumentParser(description="Initialize the host activity progress database once")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--import-json", type=Path)
    source.add_argument("--initialize-empty", action="store_true")
    args = parser.parse_args()
    payload = {}
    if args.import_json is not None:
        with args.import_json.open(encoding="utf-8") as stream:
            payload = json.load(stream)
        if not isinstance(payload, dict) or (payload and payload.get("version") != 1):
            parser.error("Unsupported activity progress JSON")
    target = database_path()
    initialized = ProgressDatabase(target).initialize(payload)
    print(f"{'Initialized' if initialized else 'Already initialized; no changes'}: {target}")


if __name__ == "__main__":
    main()
