"""
GuessMaster Pro - Statistics Manager
Tracks and persists player statistics across sessions.
"""

import json
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from game_engine import GameSession, Difficulty, GameMode


DATA_DIR  = Path(__file__).parent / "data"
STATS_FILE = DATA_DIR / "statistics.json"
HISTORY_FILE = DATA_DIR / "history.json"


class StatisticsManager:
    """Manages per-player statistics and full game history."""

    def __init__(self):
        DATA_DIR.mkdir(exist_ok=True)
        self._stats:   dict = self._load_json(STATS_FILE,  self._default_stats())
        self._history: list = self._load_json(HISTORY_FILE, [])
        self._streak   = self._stats.get("current_streak", 0)

    # ─────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────

    def record_session(self, session: GameSession) -> None:
        """Persist results from a completed GameSession."""
        s = self._stats

        s["games_played"] += 1
        s["total_attempts"] += session.attempts_used

        if session.won:
            s["wins"] += 1
            self._streak += 1
            s["current_streak"] = self._streak
            s["best_streak"]    = max(s["best_streak"], self._streak)
            s["total_score"]    += session.score

            if s["best_score"] == 0 or session.score > s["best_score"]:
                s["best_score"] = session.score

            if s["best_attempts"] == 0 or session.attempts_used < s["best_attempts"]:
                s["best_attempts"] = session.attempts_used
        else:
            self._streak = 0
            s["current_streak"] = 0
            s["losses"] += 1

        # History record
        record = {
            "date":       datetime.now().strftime("%Y-%m-%d %H:%M"),
            "player":     session.player_name,
            "difficulty": session.difficulty.label,
            "mode":       session.mode.value,
            "target":     session.target,
            "guesses":    [g.guess for g in session.guesses],
            "attempts":   session.attempts_used,
            "result":     "Win" if session.won else "Loss",
            "score":      session.score,
            "duration":   round(session.elapsed_seconds, 1),
        }
        self._history.insert(0, record)
        if len(self._history) > 500:          # cap history
            self._history = self._history[:500]

        self._save_json(STATS_FILE,  self._stats)
        self._save_json(HISTORY_FILE, self._history)

    @property
    def stats(self) -> dict:
        return dict(self._stats)

    @property
    def history(self) -> list:
        return list(self._history)

    @property
    def current_streak(self) -> int:
        return self._streak

    @property
    def win_rate(self) -> float:
        played = self._stats["games_played"]
        if played == 0:
            return 0.0
        return round(self._stats["wins"] / played * 100, 1)

    @property
    def avg_attempts(self) -> float:
        wins = self._stats["wins"]
        if wins == 0:
            return 0.0
        total = sum(
            r["attempts"] for r in self._history if r["result"] == "Win"
        )
        return round(total / wins, 1) if wins else 0.0

    def reset(self) -> None:
        self._stats   = self._default_stats()
        self._history = []
        self._streak  = 0
        self._save_json(STATS_FILE,  self._stats)
        self._save_json(HISTORY_FILE, self._history)

    # ─────────────────────────────────────────
    # Export
    # ─────────────────────────────────────────

    def export_history_csv(self, path: str) -> None:
        if not self._history:
            return
        keys = ["date", "player", "difficulty", "mode", "target",
                "guesses", "attempts", "result", "score", "duration"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            writer.writeheader()
            for row in self._history:
                row = dict(row)
                row["guesses"] = str(row.get("guesses", []))
                writer.writerow(row)

    def export_stats_csv(self, path: str) -> None:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Metric", "Value"])
            for k, v in self._stats.items():
                writer.writerow([k.replace("_", " ").title(), v])
            writer.writerow(["Win Rate (%)", self.win_rate])
            writer.writerow(["Avg Attempts (wins)", self.avg_attempts])

    # ─────────────────────────────────────────
    # Internals
    # ─────────────────────────────────────────

    @staticmethod
    def _default_stats() -> dict:
        return {
            "games_played":   0,
            "wins":           0,
            "losses":         0,
            "total_attempts": 0,
            "best_score":     0,
            "best_attempts":  0,
            "total_score":    0,
            "current_streak": 0,
            "best_streak":    0,
        }

    @staticmethod
    def _load_json(path: Path, default: Any) -> Any:
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
        return default

    @staticmethod
    def _save_json(path: Path, data: Any) -> None:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"[Stats] Save error: {e}")
