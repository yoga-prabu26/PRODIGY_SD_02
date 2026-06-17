"""
GuessMaster Pro - Game Engine
Core game logic, difficulty management, hint system, and achievements.
"""

import random
import time
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# ─────────────────────────────────────────────
# Enums & Constants
# ─────────────────────────────────────────────

class Difficulty(Enum):
    EASY   = ("Easy",   1,   50,  10)
    MEDIUM = ("Medium", 1,  100,   7)
    HARD   = ("Hard",   1,  500,   5)
    EXPERT = ("Expert", 1, 1000,   3)

    def __init__(self, label: str, min_val: int, max_val: int, attempts: int):
        self.label    = label
        self.min_val  = min_val
        self.max_val  = max_val
        self.max_attempts = attempts

    @property
    def range_label(self) -> str:
        return f"{self.min_val} – {self.max_val}"

    @classmethod
    def from_label(cls, label: str) -> "Difficulty":
        for d in cls:
            if d.label == label:
                return d
        return cls.MEDIUM


class GameMode(Enum):
    CLASSIC   = "Classic"
    CHALLENGE = "Challenge"
    TIME_ATTACK = "Time Attack"


class HintLevel(Enum):
    EXACT     = "🎯 Exact!"
    WITHIN_2  = "🔥 Within 2!"
    WITHIN_5  = "⚡ Within 5!"
    WITHIN_10 = "📍 Within 10!"
    CLOSE     = "👀 Getting Close"
    FAR       = "🌍 Way Off"

    # direction hints
    FAR_ABOVE  = "📈 Far Above"
    FAR_BELOW  = "📉 Far Below"
    ABOVE      = "⬆ Too High"
    BELOW      = "⬇ Too Low"


# ─────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────

@dataclass
class GuessResult:
    guess: int
    target: int
    attempt_number: int
    hint: str
    direction: str       # "correct", "high", "low"
    distance: int
    timestamp: float = field(default_factory=time.time)

    @property
    def is_correct(self) -> bool:
        return self.direction == "correct"


@dataclass
class GameSession:
    player_name:  str
    difficulty:   Difficulty
    mode:         GameMode
    target:       int
    max_attempts: Optional[int]
    time_limit:   Optional[int]   # seconds, None = no limit

    guesses:      list = field(default_factory=list)
    start_time:   float = field(default_factory=time.time)
    end_time:     Optional[float] = None
    won:          bool = False
    active:       bool = True

    @property
    def attempts_used(self) -> int:
        return len(self.guesses)

    @property
    def attempts_remaining(self) -> Optional[int]:
        if self.max_attempts is None:
            return None
        return max(0, self.max_attempts - self.attempts_used)

    @property
    def elapsed_seconds(self) -> float:
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time

    @property
    def time_remaining(self) -> Optional[float]:
        if self.time_limit is None:
            return None
        return max(0.0, self.time_limit - self.elapsed_seconds)

    @property
    def score(self) -> int:
        if not self.won:
            return 0
        base     = self.difficulty.max_val
        attempts = max(1, self.attempts_used)
        time_bonus = max(0, int(60 - self.elapsed_seconds)) if self.mode == GameMode.TIME_ATTACK else 0
        return max(1, int(base / attempts * 100) + time_bonus)


# ─────────────────────────────────────────────
# Achievement Definitions
# ─────────────────────────────────────────────

ACHIEVEMENTS = {
    "first_win": {
        "id":    "first_win",
        "name":  "First Win",
        "icon":  "🏆",
        "desc":  "Win your first game",
    },
    "perfect_guess": {
        "id":    "perfect_guess",
        "name":  "Perfect Guess",
        "icon":  "🎯",
        "desc":  "Guess correctly on the first try",
    },
    "win_streak_3": {
        "id":    "win_streak_3",
        "name":  "On Fire",
        "icon":  "🔥",
        "desc":  "Win 3 games in a row",
    },
    "speed_runner": {
        "id":    "speed_runner",
        "name":  "Speed Runner",
        "icon":  "⚡",
        "desc":  "Win a Time Attack game under 20 seconds",
    },
    "guess_master": {
        "id":    "guess_master",
        "name":  "Guess Master",
        "icon":  "👑",
        "desc":  "Win 10 games total",
    },
    "hard_win": {
        "id":    "hard_win",
        "name":  "Hard Boiled",
        "icon":  "💎",
        "desc":  "Win on Hard or Expert difficulty",
    },
    "challenger": {
        "id":    "challenger",
        "name":  "The Challenger",
        "icon":  "🛡",
        "desc":  "Win a Challenge Mode game",
    },
}


# ─────────────────────────────────────────────
# Game Engine
# ─────────────────────────────────────────────

class GameEngine:
    """Central game engine handling game state, guesses, hints, and achievements."""

    TIME_ATTACK_LIMIT = 60  # seconds

    def __init__(self):
        self.session: Optional[GameSession] = None

    # ── Session management ──────────────────

    def new_game(
        self,
        player_name: str,
        difficulty: Difficulty,
        mode: GameMode,
    ) -> GameSession:
        target = random.randint(difficulty.min_val, difficulty.max_val)

        max_attempts = None
        time_limit   = None

        if mode == GameMode.CHALLENGE:
            max_attempts = difficulty.max_attempts
        elif mode == GameMode.TIME_ATTACK:
            time_limit = self.TIME_ATTACK_LIMIT

        self.session = GameSession(
            player_name  = player_name,
            difficulty   = difficulty,
            mode         = mode,
            target       = target,
            max_attempts = max_attempts,
            time_limit   = time_limit,
        )
        return self.session

    def end_session(self):
        if self.session:
            self.session.active   = False
            self.session.end_time = time.time()

    # ── Core guess logic ────────────────────

    def make_guess(self, value: int) -> GuessResult:
        """Process a player guess and return a full GuessResult."""
        if self.session is None:
            raise RuntimeError("No active game session.")
        if not self.session.active:
            raise RuntimeError("Game session is not active.")

        s      = self.session
        target = s.target

        distance = abs(value - target)

        if value == target:
            direction = "correct"
            hint      = self._build_hint(distance, direction, value, target)
            s.won     = True
            s.active  = False
            s.end_time = time.time()
        elif value > target:
            direction = "high"
            hint      = self._build_hint(distance, direction, value, target)
        else:
            direction = "low"
            hint      = self._build_hint(distance, direction, value, target)

        result = GuessResult(
            guess          = value,
            target         = target,
            attempt_number = s.attempts_used + 1,
            hint           = hint,
            direction      = direction,
            distance       = distance,
        )
        s.guesses.append(result)

        # Check loss conditions
        if not s.won:
            if s.max_attempts is not None and s.attempts_used >= s.max_attempts:
                s.active  = False
                s.end_time = time.time()
            elif s.time_limit is not None and (s.time_remaining or 0) <= 0:
                s.active  = False
                s.end_time = time.time()

        return result

    # ── Hint engine ─────────────────────────

    def _build_hint(self, distance: int, direction: str, guess: int, target: int) -> str:
        if direction == "correct":
            return HintLevel.EXACT.value

        pct = distance / target if target else 1.0

        if distance <= 2:
            proximity = HintLevel.WITHIN_2.value
        elif distance <= 5:
            proximity = HintLevel.WITHIN_5.value
        elif distance <= 10:
            proximity = HintLevel.WITHIN_10.value
        elif pct <= 0.15:
            proximity = HintLevel.CLOSE.value
        else:
            proximity = HintLevel.FAR.value

        if direction == "high":
            dir_hint = HintLevel.FAR_ABOVE.value if pct > 0.3 else HintLevel.ABOVE.value
        else:
            dir_hint = HintLevel.FAR_BELOW.value if pct > 0.3 else HintLevel.BELOW.value

        return f"{dir_hint}  ·  {proximity}"

    # ── Achievement checker ──────────────────

    def check_achievements(self, stats: dict, streak: int) -> list[str]:
        """Return list of newly unlocked achievement IDs based on session result."""
        if self.session is None or not self.session.won:
            return []

        s       = self.session
        unlocked = []

        total_wins = stats.get("wins", 0)

        if total_wins == 1:
            unlocked.append("first_win")

        if s.attempts_used == 1:
            unlocked.append("perfect_guess")

        if streak >= 3:
            unlocked.append("win_streak_3")

        if (s.mode == GameMode.TIME_ATTACK and s.elapsed_seconds < 20):
            unlocked.append("speed_runner")

        if total_wins >= 10:
            unlocked.append("guess_master")

        if s.difficulty in (Difficulty.HARD, Difficulty.EXPERT):
            unlocked.append("hard_win")

        if s.mode == GameMode.CHALLENGE:
            unlocked.append("challenger")

        return unlocked

    # ── Utility ─────────────────────────────

    def validate_guess(self, raw: str) -> tuple[bool, Optional[int], str]:
        """Validate raw input string. Returns (valid, value, error_msg)."""
        raw = raw.strip()
        if not raw:
            return False, None, "Please enter a number."
        try:
            value = int(raw)
        except ValueError:
            return False, None, "Whole numbers only, please."

        if self.session:
            lo = self.session.difficulty.min_val
            hi = self.session.difficulty.max_val
            if not (lo <= value <= hi):
                return False, None, f"Must be between {lo} and {hi}."

        return True, value, ""
