"""
GuessMaster Pro - Achievement Manager
Tracks and persists unlocked achievements.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from game_engine import ACHIEVEMENTS


DATA_DIR         = Path(__file__).parent / "data"
ACHIEVEMENTS_FILE = DATA_DIR / "achievements.json"


class AchievementManager:
    """Tracks which achievements the player has unlocked."""

    def __init__(self):
        DATA_DIR.mkdir(exist_ok=True)
        self._unlocked: dict[str, str] = self._load()   # id -> date string

    # ─────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────

    def unlock_batch(self, ids: list[str]) -> list[dict]:
        """
        Unlock a list of achievement IDs (if not already unlocked).
        Returns list of newly-unlocked achievement dicts.
        """
        newly = []
        for aid in ids:
            if aid not in self._unlocked and aid in ACHIEVEMENTS:
                self._unlocked[aid] = datetime.now().strftime("%Y-%m-%d")
                newly.append(ACHIEVEMENTS[aid])
        if newly:
            self._save()
        return newly

    @property
    def unlocked_ids(self) -> set[str]:
        return set(self._unlocked.keys())

    def all_achievements(self) -> list[dict]:
        """Return all achievements enriched with unlock status."""
        result = []
        for aid, data in ACHIEVEMENTS.items():
            entry = dict(data)
            entry["unlocked"] = aid in self._unlocked
            entry["date"]     = self._unlocked.get(aid, "")
            result.append(entry)
        return result

    def reset(self) -> None:
        self._unlocked = {}
        self._save()

    # ─────────────────────────────────────────
    # Internals
    # ─────────────────────────────────────────

    def _load(self) -> dict:
        try:
            if ACHIEVEMENTS_FILE.exists():
                with open(ACHIEVEMENTS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
        return {}

    def _save(self) -> None:
        try:
            with open(ACHIEVEMENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._unlocked, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"[Achievements] Save error: {e}")
