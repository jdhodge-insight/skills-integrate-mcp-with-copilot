"""Database access helpers for the activities API.

This module provides a tiny SQLite-backed persistence layer so activity and
participant data survives process restarts.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, Any


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "activities.db"


INITIAL_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"],
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"],
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"],
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"],
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"],
    },
}


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    """Create schema and seed initial data if this is a fresh database."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                schedule TEXT NOT NULL,
                max_participants INTEGER NOT NULL CHECK(max_participants > 0)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_participants (
                activity_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                PRIMARY KEY (activity_id, email),
                FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
            )
            """
        )

        existing_activity_count = cursor.execute(
            "SELECT COUNT(*) FROM activities"
        ).fetchone()[0]
        if existing_activity_count == 0:
            _seed_initial_data(cursor)

        connection.commit()


def _seed_initial_data(cursor: sqlite3.Cursor) -> None:
    for activity_name, details in INITIAL_ACTIVITIES.items():
        cursor.execute(
            """
            INSERT INTO activities (name, description, schedule, max_participants)
            VALUES (?, ?, ?, ?)
            """,
            (
                activity_name,
                details["description"],
                details["schedule"],
                details["max_participants"],
            ),
        )
        activity_id = cursor.lastrowid
        for email in details["participants"]:
            cursor.execute(
                """
                INSERT INTO activity_participants (activity_id, email)
                VALUES (?, ?)
                """,
                (activity_id, email),
            )


def list_activities() -> Dict[str, Dict[str, Any]]:
    """Return activities in the same shape as the original in-memory API."""
    with _connect() as connection:
        cursor = connection.cursor()
        rows = cursor.execute(
            """
            SELECT
                a.id,
                a.name,
                a.description,
                a.schedule,
                a.max_participants,
                ap.email
            FROM activities a
            LEFT JOIN activity_participants ap ON ap.activity_id = a.id
            ORDER BY a.name, ap.email
            """
        ).fetchall()

    activities: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        name = row["name"]
        if name not in activities:
            activities[name] = {
                "description": row["description"],
                "schedule": row["schedule"],
                "max_participants": row["max_participants"],
                "participants": [],
            }
        if row["email"] is not None:
            activities[name]["participants"].append(row["email"])

    return activities


def signup_for_activity(activity_name: str, email: str) -> str:
    """Add an email participant to an activity.

    Raises:
        KeyError: Activity does not exist.
        ValueError: Participant already registered or activity is full.
    """
    with _connect() as connection:
        cursor = connection.cursor()
        activity = cursor.execute(
            """
            SELECT id, max_participants
            FROM activities
            WHERE name = ?
            """,
            (activity_name,),
        ).fetchone()
        if activity is None:
            raise KeyError("Activity not found")

        existing_registration = cursor.execute(
            """
            SELECT 1
            FROM activity_participants
            WHERE activity_id = ? AND email = ?
            """,
            (activity["id"], email),
        ).fetchone()
        if existing_registration is not None:
            raise ValueError("Student is already signed up")

        current_count = cursor.execute(
            """
            SELECT COUNT(*)
            FROM activity_participants
            WHERE activity_id = ?
            """,
            (activity["id"],),
        ).fetchone()[0]
        if current_count >= activity["max_participants"]:
            raise ValueError("Activity is already full")

        cursor.execute(
            """
            INSERT INTO activity_participants (activity_id, email)
            VALUES (?, ?)
            """,
            (activity["id"], email),
        )
        connection.commit()

    return f"Signed up {email} for {activity_name}"


def unregister_from_activity(activity_name: str, email: str) -> str:
    """Remove an email participant from an activity.

    Raises:
        KeyError: Activity does not exist.
        ValueError: Participant is not registered.
    """
    with _connect() as connection:
        cursor = connection.cursor()
        activity = cursor.execute(
            """
            SELECT id
            FROM activities
            WHERE name = ?
            """,
            (activity_name,),
        ).fetchone()
        if activity is None:
            raise KeyError("Activity not found")

        deleted_rows = cursor.execute(
            """
            DELETE FROM activity_participants
            WHERE activity_id = ? AND email = ?
            """,
            (activity["id"], email),
        ).rowcount
        if deleted_rows == 0:
            raise ValueError("Student is not signed up for this activity")

        connection.commit()

    return f"Unregistered {email} from {activity_name}"