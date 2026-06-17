"""
GuessMaster Pro - Leaderboard Manager
Top-10 score tracking with local JSON persistence.
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from game_engine import GameSession


DATA_DIR        = Path(__file__).parent / "data"
LEADERBOARD_FILE = DATA_DIR / "leaderboard.json"
TOP_N           = 10


class LeaderboardManager:
    """Manages the top-10 leaderboard with local persistence."""

    def __init__(self):
        DATA_DIR.mkdir(exist_ok=True)
        self._entries: list[dict] = self._load()

    # ─────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────

    def submit(self, session: GameSession) -> tuple[bool, int]:
        """
        Submit a completed session.
        Returns (made_leaderboard, rank) — rank is 1-based, 0 if not on board.
        """
        if not session.won:
            return False, 0

        entry = {
            "player":     session.player_name,
            "score":      session.score,
            "difficulty": session.difficulty.label,
            "mode":       session.mode.value,
            "attempts":   session.attempts_used,
            "duration":   round(session.elapsed_seconds, 1),
            "date":       datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        self._entries.append(entry)
        self._entries.sort(key=lambda e: e["score"], reverse=True)
        self._entries = self._entries[:TOP_N]
        self._save()

        if entry in self._entries:
            rank = self._entries.index(entry) + 1
            return True, rank
        return False, 0

    @property
    def entries(self) -> list[dict]:
        return list(self._entries)

    def reset(self) -> None:
        self._entries = []
        self._save()

    # ─────────────────────────────────────────
    # Export
    # ─────────────────────────────────────────

    def export_csv(self, path: str) -> None:
        if not self._entries:
            return
        keys = ["player", "score", "difficulty", "mode",
                "attempts", "duration", "date"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(self._entries)

    # ─────────────────────────────────────────
    # Internals
    # ─────────────────────────────────────────

    def _load(self) -> list[dict]:
        try:
            if LEADERBOARD_FILE.exists():
                with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
        return []

    def _save(self) -> None:
        try:
            with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
                json.dump(self._entries, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"[Leaderboard] Save error: {e}")
