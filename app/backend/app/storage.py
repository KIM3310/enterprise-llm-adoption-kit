import os
import sqlite3
from datetime import datetime
from typing import Optional

from .config import settings


def init_db() -> None:
    os.makedirs(os.path.dirname(settings.sqlite_path), exist_ok=True)
    conn = sqlite3.connect(settings.sqlite_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_costs (
                day TEXT PRIMARY KEY,
                total_cost REAL NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def add_cost(amount: float) -> None:
    day = datetime.utcnow().strftime("%Y-%m-%d")
    conn = sqlite3.connect(settings.sqlite_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO daily_costs(day, total_cost) VALUES(?, ?) "
            "ON CONFLICT(day) DO UPDATE SET total_cost = total_cost + ?",
            (day, amount, amount),
        )
        conn.commit()
    finally:
        conn.close()


def get_daily_cost(day: Optional[str] = None) -> float:
    if day is None:
        day = datetime.utcnow().strftime("%Y-%m-%d")
    conn = sqlite3.connect(settings.sqlite_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT total_cost FROM daily_costs WHERE day = ?", (day,))
        row = cur.fetchone()
        return float(row[0]) if row else 0.0
    finally:
        conn.close()
