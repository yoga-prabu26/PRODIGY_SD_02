"""
GuessMaster Pro - UI
Full Tkinter GUI: dark theme, dashboard layout, all panels.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from typing import Optional, Callable

from game_engine import (
    GameEngine, Difficulty, GameMode, GuessResult, GameSession
)
from statistics   import StatisticsManager
from leaderboard  import LeaderboardManager
from achievements import AchievementManager


# ─────────────────────────────────────────────
# Design Tokens
# ─────────────────────────────────────────────

COLORS = {
    # Backgrounds
    "bg_deep":   "#0D0F14",
    "bg_panel":  "#13161E",
    "bg_card":   "#1C2030",
    "bg_input":  "#252A3A",
    "bg_hover":  "#2A3045",

    # Accents
    "accent":    "#6C63FF",   # electric violet — signature hue
    "accent2":   "#00D4AA",   # teal for success/correct
    "accent3":   "#FF6B6B",   # coral for wrong/high
    "accent4":   "#FFD166",   # amber for warnings/low
    "accent5":   "#A78BFA",   # soft violet for secondary

    # Text
    "text_primary":   "#F0F2FF",
    "text_secondary": "#8892B0",
    "text_muted":     "#4A5568",
    "text_accent":    "#6C63FF",

    # Borders
    "border":    "#252A3A",
    "border_active": "#6C63FF",

    # Specials
    "correct":   "#00D4AA",
    "too_high":  "#FF6B6B",
    "too_low":   "#FFD166",
    "disabled":  "#2D3348",
}

FONTS = {
    "display":  ("Segoe UI", 28, "bold"),
    "heading":  ("Segoe UI", 16, "bold"),
    "subhead":  ("Segoe UI", 12, "bold"),
    "body":     ("Segoe UI", 11),
    "body_b":   ("Segoe UI", 11, "bold"),
    "small":    ("Segoe UI", 9),
    "small_b":  ("Segoe UI", 9, "bold"),
    "mono":     ("Consolas",  13, "bold"),
    "number":   ("Segoe UI",  36, "bold"),
    "score":    ("Segoe UI",  22, "bold"),
    "stat_value": ("Segoe UI", 16, "bold"),
    "hint":     ("Segoe UI",  13, "bold"),
    "emoji":    ("Segoe UI Emoji", 20),
}

PAD = {"padx": 12, "pady": 8}


# ─────────────────────────────────────────────
# Reusable Widget Helpers
# ─────────────────────────────────────────────

def card(parent, **kw) -> tk.Frame:
    return tk.Frame(
        parent,
        bg=COLORS["bg_card"],
        bd=0,
        highlightthickness=1,
        highlightbackground=COLORS["border"],
        **kw
    )


def label(parent, text="", style="body", fg=None, **kw) -> tk.Label:
    font = FONTS.get(style, FONTS["body"])
    color = fg or COLORS["text_primary"]
    return tk.Label(parent, text=text, font=font,
                    fg=color, bg=parent["bg"], **kw)


def accent_button(parent, text, command, width=18, color=None) -> tk.Button:
    bg = color or COLORS["accent"]
    btn = tk.Button(
        parent, text=text, command=command,
        font=FONTS["body_b"],
        fg=COLORS["text_primary"],
        bg=bg,
        activebackground=COLORS["accent5"],
        activeforeground=COLORS["text_primary"],
        relief="flat", bd=0, cursor="hand2",
        width=width, pady=8,
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=COLORS["accent5"]))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg))
    return btn


def ghost_button(parent, text, command, width=14) -> tk.Button:
    btn = tk.Button(
        parent, text=text, command=command,
        font=FONTS["small_b"],
        fg=COLORS["text_secondary"],
        bg=COLORS["bg_card"],
        activebackground=COLORS["bg_hover"],
        activeforeground=COLORS["text_primary"],
        relief="flat", bd=0, cursor="hand2",
        width=width, pady=6,
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=COLORS["bg_hover"], fg=COLORS["text_primary"]))
    btn.bind("<Leave>", lambda e: btn.config(bg=COLORS["bg_card"], fg=COLORS["text_secondary"]))
    return btn


def sep(parent):
    tk.Frame(parent, bg=COLORS["border"], height=1).pack(fill="x", padx=0, pady=4)


# ─────────────────────────────────────────────
# Stat Card
# ─────────────────────────────────────────────

class StatCard(tk.Frame):
    """Compact stat display card — sized to fit dense sidebar grids."""

    def __init__(self, parent, title, value="—", accent=None):
        super().__init__(parent, bg=COLORS["bg_card"],
                         highlightthickness=1,
                         highlightbackground=COLORS["border"])
        accent = accent or COLORS["accent"]
        # top accent bar
        tk.Frame(self, bg=accent, height=2).pack(fill="x")
        inner = tk.Frame(self, bg=COLORS["bg_card"])
        inner.pack(fill="both", expand=True, padx=8, pady=6)
        self._val_lbl = tk.Label(inner, text=str(value), font=FONTS["stat_value"],
                                 fg=accent, bg=COLORS["bg_card"])
        self._val_lbl.pack(anchor="w")
        tk.Label(inner, text=title, font=FONTS["small"],
                 fg=COLORS["text_secondary"], bg=COLORS["bg_card"],
                 wraplength=90, justify="left").pack(anchor="w")

    def update_value(self, value):
        self._val_lbl.config(text=str(value))


# ─────────────────────────────────────────────
# Guess History Row
# ─────────────────────────────────────────────

class GuessRow(tk.Frame):
    DIR_COLORS = {
        "correct": COLORS["correct"],
        "high":    COLORS["too_high"],
        "low":     COLORS["too_low"],
    }
    DIR_ICONS = {"correct": "✓", "high": "▲", "low": "▼"}

    def __init__(self, parent, result: GuessResult):
        bg = COLORS["bg_input"] if result.attempt_number % 2 == 0 else COLORS["bg_card"]
        super().__init__(parent, bg=bg)
        color = self.DIR_COLORS.get(result.direction, COLORS["text_secondary"])
        icon  = self.DIR_ICONS.get(result.direction, "?")

        tk.Label(self, text=f"#{result.attempt_number:>2}", font=FONTS["small"],
                 fg=COLORS["text_muted"], bg=bg, width=4).pack(side="left", padx=(8, 4))
        tk.Label(self, text=f"{result.guess:>5}", font=FONTS["mono"],
                 fg=color, bg=bg).pack(side="left", padx=4)
        tk.Label(self, text=icon, font=FONTS["body_b"],
                 fg=color, bg=bg, width=3).pack(side="left")
        tk.Label(self, text=result.hint, font=FONTS["small"],
                 fg=COLORS["text_secondary"], bg=bg).pack(side="left", padx=8)

        self.pack(fill="x", pady=1)


# ─────────────────────────────────────────────
# Achievement Badge
# ─────────────────────────────────────────────

class AchievementBadge(tk.Frame):
    def __init__(self, parent, data: dict):
        unlocked = data.get("unlocked", False)
        bg = COLORS["bg_card"]
        super().__init__(parent, bg=bg, highlightthickness=1,
                         highlightbackground=COLORS["accent"] if unlocked else COLORS["border"])
        alpha = COLORS["text_primary"] if unlocked else COLORS["text_muted"]
        icon_color = COLORS["accent"] if unlocked else COLORS["text_muted"]

        tk.Label(self, text=data["icon"], font=("Segoe UI Emoji", 18),
                 fg=icon_color, bg=bg).pack(pady=(10, 2))
        tk.Label(self, text=data["name"], font=FONTS["small_b"],
                 fg=alpha, bg=bg).pack()
        tk.Label(self, text=data["desc"], font=FONTS["small"],
                 fg=COLORS["text_muted"], bg=bg, wraplength=90,
                 justify="center").pack(padx=6, pady=(2, 8))
        if unlocked and data.get("date"):
            tk.Label(self, text=data["date"], font=FONTS["small"],
                     fg=COLORS["accent5"], bg=bg).pack(pady=(0, 6))


# ─────────────────────────────────────────────
# Main Application Window
# ─────────────────────────────────────────────

class GuessMasterApp(tk.Tk):
    """Root window and application controller."""

    def __init__(self):
        super().__init__()
        self.title("GuessMaster Pro")
        self.geometry("1280x760")
        self.minsize(1024, 650)
        self.configure(bg=COLORS["bg_deep"])
        self.resizable(True, True)

        # Services
        self.engine   = GameEngine()
        self.stats_mgr = StatisticsManager()
        self.lb_mgr   = LeaderboardManager()
        self.ach_mgr  = AchievementManager()

        # State
        self._player_name = tk.StringVar(value="Player")
        self._difficulty  = tk.StringVar(value=Difficulty.MEDIUM.label)
        self._mode        = tk.StringVar(value=GameMode.CLASSIC.value)
        self._sound_on    = tk.BooleanVar(value=True)
        self._timer_job: Optional[str] = None
        self._active_tab  = tk.StringVar(value="game")

        self._build_ui()
        self._refresh_stats_panel()
        self._refresh_leaderboard()
        self._refresh_achievements()

    # ─────────────────────────────────────────
    # UI Construction
    # ─────────────────────────────────────────

    def _build_ui(self):
        # ── Title bar ─────────────────────────
        titlebar = tk.Frame(self, bg=COLORS["bg_panel"], pady=0)
        titlebar.pack(fill="x")

        # Logo section
        logo_f = tk.Frame(titlebar, bg=COLORS["bg_panel"])
        logo_f.pack(side="left", padx=20, pady=12)
        tk.Label(logo_f, text="🎯", font=("Segoe UI Emoji", 20),
                 bg=COLORS["bg_panel"], fg=COLORS["accent"]).pack(side="left")
        tk.Label(logo_f, text=" GuessMaster", font=("Segoe UI", 16, "bold"),
                 bg=COLORS["bg_panel"], fg=COLORS["text_primary"]).pack(side="left")
        tk.Label(logo_f, text=" Pro", font=("Segoe UI", 16, "bold"),
                 bg=COLORS["bg_panel"], fg=COLORS["accent"]).pack(side="left")

        # Nav tabs
        nav_f = tk.Frame(titlebar, bg=COLORS["bg_panel"])
        nav_f.pack(side="left", padx=40)
        for tab_id, label_text in [
            ("game",        "▶  Play"),
            ("leaderboard", "🏆  Leaderboard"),
            ("history",     "📋  History"),
            ("achievements","🎖  Achievements"),
            ("settings",    "⚙  Settings"),
        ]:
            self._nav_tab(nav_f, tab_id, label_text)

        # Player name chip
        right_f = tk.Frame(titlebar, bg=COLORS["bg_panel"])
        right_f.pack(side="right", padx=20)
        tk.Label(right_f, text="👤", font=("Segoe UI Emoji", 12),
                 bg=COLORS["bg_panel"], fg=COLORS["accent5"]).pack(side="left")
        name_entry = tk.Entry(right_f, textvariable=self._player_name,
                              font=FONTS["body_b"], fg=COLORS["text_primary"],
                              bg=COLORS["bg_input"], relief="flat",
                              insertbackground=COLORS["text_primary"], width=14)
        name_entry.pack(side="left", padx=(4, 0), ipady=4)

        # ── Content area ──────────────────────
        self._content = tk.Frame(self, bg=COLORS["bg_deep"])
        self._content.pack(fill="both", expand=True)

        # Build all views (only one shown at a time)
        self._views: dict[str, tk.Frame] = {}
        self._build_game_view()
        self._build_leaderboard_view()
        self._build_history_view()
        self._build_achievements_view()
        self._build_settings_view()

        self._show_tab("game")

    def _nav_tab(self, parent, tab_id, text):
        btn = tk.Button(
            parent, text=text,
            font=FONTS["small_b"],
            fg=COLORS["text_secondary"],
            bg=COLORS["bg_panel"],
            activebackground=COLORS["bg_hover"],
            activeforeground=COLORS["text_primary"],
            relief="flat", bd=0, cursor="hand2",
            padx=14, pady=14,
            command=lambda t=tab_id: self._show_tab(t),
        )
        btn.pack(side="left")

        def on_enter(e): btn.config(fg=COLORS["text_primary"])
        def on_leave(e): btn.config(fg=COLORS["text_secondary"])
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    def _show_tab(self, tab_id: str):
        self._active_tab.set(tab_id)
        for vid, view in self._views.items():
            if vid == tab_id:
                view.pack(fill="both", expand=True)
            else:
                view.pack_forget()

        if tab_id == "history":
            self._refresh_history_panel()
        elif tab_id == "leaderboard":
            self._refresh_leaderboard()
        elif tab_id == "achievements":
            self._refresh_achievements()

    # ─────────────────────────────────────────
    # GAME VIEW
    # ─────────────────────────────────────────

    def _build_game_view(self):
        view = tk.Frame(self._content, bg=COLORS["bg_deep"])
        self._views["game"] = view

        # Left sidebar: config + stats — width scales with screen size
        screen_w = self.winfo_screenwidth()
        sidebar_w = 230 if screen_w <= 1366 else 270
        sidebar = tk.Frame(view, bg=COLORS["bg_panel"], width=sidebar_w)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self._build_sidebar(sidebar)

        # Right: main game + guess history
        main_area = tk.Frame(view, bg=COLORS["bg_deep"])
        main_area.pack(side="left", fill="both", expand=True)

        # Game panel (top)
        game_panel = tk.Frame(main_area, bg=COLORS["bg_deep"])
        game_panel.pack(fill="x", padx=16, pady=(12, 0))
        self._build_game_panel(game_panel)

        # History panel (bottom, scrollable)
        hist_frame = card(main_area)
        hist_frame.pack(fill="both", expand=True, padx=16, pady=12)
        self._build_inline_history(hist_frame)

    def _build_sidebar(self, parent):
        tk.Frame(parent, bg=COLORS["border"], height=1).pack(fill="x")

        scroll_outer = tk.Frame(parent, bg=COLORS["bg_panel"])
        scroll_outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(scroll_outer, bg=COLORS["bg_panel"],
                           bd=0, highlightthickness=0)
        sb = ttk.Scrollbar(scroll_outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=COLORS["bg_panel"])
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win_id, width=canvas.winfo_width())
        inner.bind("<Configure>", on_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))

        p = {"padx": 14, "pady": 2}

        # ── Section: New Game ─────────────────
        tk.Label(inner, text="NEW GAME", font=FONTS["small_b"],
                 fg=COLORS["text_muted"], bg=COLORS["bg_panel"]).pack(anchor="w", padx=14, pady=(12, 2))

        sep(inner)

        tk.Label(inner, text="Difficulty", font=FONTS["small_b"],
                 fg=COLORS["text_secondary"], bg=COLORS["bg_panel"]).pack(anchor="w", **p)
        for diff in Difficulty:
            rb = tk.Radiobutton(
                inner, text=f"{diff.label}  ({diff.range_label})",
                variable=self._difficulty, value=diff.label,
                font=FONTS["small"], fg=COLORS["text_primary"],
                bg=COLORS["bg_panel"],
                selectcolor=COLORS["bg_card"],
                activebackground=COLORS["bg_panel"],
                activeforeground=COLORS["accent"],
                cursor="hand2",
            )
            rb.pack(anchor="w", padx=20, pady=0)

        sep(inner)

        tk.Label(inner, text="Game Mode", font=FONTS["small_b"],
                 fg=COLORS["text_secondary"], bg=COLORS["bg_panel"]).pack(anchor="w", **p)

        mode_descs = {
            GameMode.CLASSIC:    "Unlimited attempts",
            GameMode.CHALLENGE:  "Limited attempts",
            GameMode.TIME_ATTACK: "60-second countdown",
        }
        for mode in GameMode:
            rb = tk.Radiobutton(
                inner, text=f"{mode.value} — {mode_descs[mode]}",
                variable=self._mode, value=mode.value,
                font=FONTS["small"], fg=COLORS["text_primary"],
                bg=COLORS["bg_panel"],
                selectcolor=COLORS["bg_card"],
                activebackground=COLORS["bg_panel"],
                activeforeground=COLORS["accent"],
                cursor="hand2", justify="left", wraplength=190,
            )
            rb.pack(anchor="w", padx=20, pady=0)

        sep(inner)

        start_btn = accent_button(inner, "▶  Start New Game", self._start_game, width=22)
        start_btn.pack(padx=14, pady=6, fill="x")

        sep(inner)

        # ── Section: Live Stats ───────────────
        tk.Label(inner, text="SESSION STATS", font=FONTS["small_b"],
                 fg=COLORS["text_muted"], bg=COLORS["bg_panel"]).pack(anchor="w", padx=14, pady=(4, 2))

        stats_grid = tk.Frame(inner, bg=COLORS["bg_panel"])
        stats_grid.pack(fill="x", padx=10, pady=2)

        self._sc_attempts   = StatCard(stats_grid, "Attempts",   "0",  COLORS["accent"])
        self._sc_remaining  = StatCard(stats_grid, "Left",       "—",  COLORS["accent2"])
        self._sc_best       = StatCard(stats_grid, "Best",       "—",  COLORS["accent4"])
        self._sc_winrate    = StatCard(stats_grid, "Win %",      "0%", COLORS["accent3"])
        self._sc_avg        = StatCard(stats_grid, "Avg Tries",  "—",  COLORS["accent5"])
        self._sc_played     = StatCard(stats_grid, "Played",     "0",  COLORS["text_secondary"])

        for i, sc in enumerate([
            self._sc_attempts, self._sc_remaining, self._sc_best,
            self._sc_winrate, self._sc_avg, self._sc_played,
        ]):
            sc.grid(row=i // 3, column=i % 3, padx=2, pady=2, sticky="nsew")
        for c in range(3):
            stats_grid.columnconfigure(c, weight=1)

        sep(inner)

        # Export buttons
        tk.Label(inner, text="EXPORT", font=FONTS["small_b"],
                 fg=COLORS["text_muted"], bg=COLORS["bg_panel"]).pack(anchor="w", padx=14, pady=(2, 2))
        ef = tk.Frame(inner, bg=COLORS["bg_panel"])
        ef.pack(fill="x", padx=10, pady=(0, 12))
        ghost_button(ef, "History",    self._export_history, width=10).pack(side="left", padx=2, fill="x", expand=True)
        ghost_button(ef, "Leaderboard", self._export_leaderboard, width=10).pack(side="left", padx=2, fill="x", expand=True)

    def _build_game_panel(self, parent):
        # Top info row: difficulty, mode, timer
        info_row = tk.Frame(parent, bg=COLORS["bg_deep"])
        info_row.pack(fill="x", pady=(0, 8))

        self._lbl_difficulty = tk.Label(
            info_row, text="", font=FONTS["small_b"],
            fg=COLORS["accent5"], bg=COLORS["bg_card"],
            padx=10, pady=4,
        )
        self._lbl_difficulty.pack(side="left", padx=(0, 8))

        self._lbl_mode = tk.Label(
            info_row, text="", font=FONTS["small_b"],
            fg=COLORS["accent2"], bg=COLORS["bg_card"],
            padx=10, pady=4,
        )
        self._lbl_mode.pack(side="left", padx=(0, 8))

        self._lbl_timer = tk.Label(
            info_row, text="", font=FONTS["score"],
            fg=COLORS["accent4"], bg=COLORS["bg_deep"],
        )
        self._lbl_timer.pack(side="right")

        # Central game card
        c = card(parent)
        c.pack(fill="x")

        inner = tk.Frame(c, bg=COLORS["bg_card"])
        inner.pack(fill="both", expand=True, padx=20, pady=14)

        # Range display
        self._lbl_range = tk.Label(
            inner, text="Start a new game to play",
            font=FONTS["subhead"],
            fg=COLORS["text_muted"], bg=COLORS["bg_card"],
        )
        self._lbl_range.pack()

        # Feedback / hint display
        self._lbl_feedback = tk.Label(
            inner, text="",
            font=FONTS["hint"],
            fg=COLORS["text_secondary"], bg=COLORS["bg_card"],
            pady=4,
        )
        self._lbl_feedback.pack()

        # Input row
        input_row = tk.Frame(inner, bg=COLORS["bg_card"])
        input_row.pack(pady=6)

        self._guess_var = tk.StringVar()

        # Dark themed input with a focus-ring border frame
        self._entry_border = tk.Frame(
            input_row, bg=COLORS["border"], padx=2, pady=2,
        )
        self._entry_border.pack(side="left", padx=(0, 12))

        self._entry = tk.Entry(
            self._entry_border, textvariable=self._guess_var,
            font=("Segoe UI", 22, "bold"),
            fg=COLORS["text_primary"], bg=COLORS["bg_input"],
            insertbackground=COLORS["accent"],
            disabledbackground=COLORS["bg_input"],
            disabledforeground=COLORS["text_muted"],
            readonlybackground=COLORS["bg_input"],
            relief="flat", bd=0, width=8, justify="center",
            state="disabled",
            highlightthickness=0,
        )
        self._entry.pack(ipady=10, ipadx=4)
        self._entry.bind("<Return>", lambda e: self._submit_guess())
        self._entry.bind("<FocusIn>", self._on_entry_focus_in)
        self._entry.bind("<FocusOut>", self._on_entry_focus_out)

        self._btn_guess = tk.Button(
            input_row, text="Guess  →",
            font=FONTS["body_b"],
            fg=COLORS["text_primary"],
            bg=COLORS["accent"],
            activebackground=COLORS["accent5"],
            activeforeground=COLORS["text_primary"],
            disabledforeground=COLORS["text_muted"],
            relief="flat", bd=0, cursor="hand2",
            padx=20, pady=11,
            command=self._submit_guess,
            state="disabled",
        )
        self._btn_guess.pack(side="left")

        # Error / validation label
        self._lbl_error = tk.Label(
            inner, text="",
            font=FONTS["small"],
            fg=COLORS["too_high"], bg=COLORS["bg_card"],
        )
        self._lbl_error.pack()

        # Progress section — label row + bar
        progress_wrap = tk.Frame(inner, bg=COLORS["bg_card"])
        progress_wrap.pack(fill="x", pady=(6, 0), padx=40)

        progress_label_row = tk.Frame(progress_wrap, bg=COLORS["bg_card"])
        progress_label_row.pack(fill="x")

        self._lbl_progress_title = tk.Label(
            progress_label_row, text="Progress",
            font=FONTS["small_b"], fg=COLORS["text_secondary"],
            bg=COLORS["bg_card"],
        )
        self._lbl_progress_title.pack(side="left")

        self._lbl_progress_value = tk.Label(
            progress_label_row, text="0%",
            font=FONTS["small_b"], fg=COLORS["accent"],
            bg=COLORS["bg_card"],
        )
        self._lbl_progress_value.pack(side="right")

        self._progress_var = tk.DoubleVar(value=0)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "GM.Horizontal.TProgressbar",
            troughcolor=COLORS["bg_input"],
            background=COLORS["accent"],
            borderwidth=0, thickness=6,
        )
        self._progress = ttk.Progressbar(
            progress_wrap, variable=self._progress_var,
            style="GM.Horizontal.TProgressbar",
            orient="horizontal", maximum=100,
        )
        self._progress.pack(fill="x", pady=(2, 0))

    # ── Entry focus ring handlers ───────────

    def _on_entry_focus_in(self, _event=None):
        self._entry_border.config(bg=COLORS["accent"])

    def _on_entry_focus_out(self, _event=None):
        self._entry_border.config(bg=COLORS["border"])

    def _build_inline_history(self, parent):
        tk.Label(parent, text="  GUESS HISTORY",
                 font=FONTS["small_b"],
                 fg=COLORS["text_muted"],
                 bg=COLORS["bg_card"]).pack(anchor="w", padx=4, pady=(8, 4))
        tk.Frame(parent, bg=COLORS["border"], height=1).pack(fill="x")

        canvas = tk.Canvas(parent, bg=COLORS["bg_card"], bd=0,
                           highlightthickness=0)
        sb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._guess_hist_frame = tk.Frame(canvas, bg=COLORS["bg_card"])
        win_id = canvas.create_window((0, 0), window=self._guess_hist_frame, anchor="nw")

        def on_cfg(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win_id, width=canvas.winfo_width())
        self._guess_hist_frame.bind("<Configure>", on_cfg)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))

        self._guess_canvas = canvas

    # ─────────────────────────────────────────
    # LEADERBOARD VIEW
    # ─────────────────────────────────────────

    def _build_leaderboard_view(self):
        view = tk.Frame(self._content, bg=COLORS["bg_deep"])
        self._views["leaderboard"] = view

        # Header
        hdr = tk.Frame(view, bg=COLORS["bg_panel"])
        hdr.pack(fill="x")
        tk.Label(hdr, text="🏆  Leaderboard  —  Top 10",
                 font=FONTS["heading"], fg=COLORS["text_primary"],
                 bg=COLORS["bg_panel"], pady=16).pack(side="left", padx=24)
        ghost_button(hdr, "Export CSV", self._export_leaderboard, width=12).pack(side="right", padx=16)

        # Table
        table_frame = card(view)
        table_frame.pack(fill="both", expand=True, padx=24, pady=16)

        cols = ("rank", "player", "score", "difficulty", "mode", "attempts", "duration", "date")
        col_labels = ("#", "Player", "Score", "Difficulty", "Mode", "Attempts", "Time (s)", "Date")
        col_widths  = (40, 150, 90, 100, 110, 90, 80, 130)

        style = ttk.Style()
        style.configure("GM.Treeview",
                        background=COLORS["bg_card"],
                        foreground=COLORS["text_primary"],
                        fieldbackground=COLORS["bg_card"],
                        rowheight=32,
                        font=FONTS["body"])
        style.configure("GM.Treeview.Heading",
                        background=COLORS["bg_input"],
                        foreground=COLORS["text_secondary"],
                        font=FONTS["small_b"])
        style.map("GM.Treeview",
                  background=[("selected", COLORS["accent"])],
                  foreground=[("selected", COLORS["text_primary"])])

        self._lb_tree = ttk.Treeview(
            table_frame, columns=cols, show="headings",
            style="GM.Treeview",
        )
        for col, lbl, w in zip(cols, col_labels, col_widths):
            self._lb_tree.heading(col, text=lbl)
            self._lb_tree.column(col, width=w, anchor="center")

        sb2 = ttk.Scrollbar(table_frame, orient="vertical", command=self._lb_tree.yview)
        self._lb_tree.configure(yscrollcommand=sb2.set)
        sb2.pack(side="right", fill="y", pady=8)
        self._lb_tree.pack(fill="both", expand=True, padx=8, pady=8)

    def _refresh_leaderboard(self):
        if not hasattr(self, "_lb_tree"):
            return
        for row in self._lb_tree.get_children():
            self._lb_tree.delete(row)

        rank_icons = {1: "🥇", 2: "🥈", 3: "🥉"}
        for i, entry in enumerate(self.lb_mgr.entries, start=1):
            icon = rank_icons.get(i, str(i))
            self._lb_tree.insert("", "end", values=(
                icon,
                entry.get("player", ""),
                f"{entry.get('score', 0):,}",
                entry.get("difficulty", ""),
                entry.get("mode", ""),
                entry.get("attempts", ""),
                entry.get("duration", ""),
                entry.get("date", ""),
            ))

    # ─────────────────────────────────────────
    # HISTORY VIEW (full, tabbed)
    # ─────────────────────────────────────────

    def _build_history_view(self):
        view = tk.Frame(self._content, bg=COLORS["bg_deep"])
        self._views["history"] = view

        hdr = tk.Frame(view, bg=COLORS["bg_panel"])
        hdr.pack(fill="x")
        tk.Label(hdr, text="📋  Game History",
                 font=FONTS["heading"], fg=COLORS["text_primary"],
                 bg=COLORS["bg_panel"], pady=16).pack(side="left", padx=24)
        ghost_button(hdr, "Export CSV", self._export_history, width=12).pack(side="right", padx=16)

        table_frame = card(view)
        table_frame.pack(fill="both", expand=True, padx=24, pady=16)

        cols = ("date", "player", "difficulty", "mode", "target",
                "attempts", "result", "score", "duration")
        col_labels = ("Date", "Player", "Diff", "Mode", "Target",
                      "Attempts", "Result", "Score", "Time (s)")
        col_widths  = (130, 100, 80, 110, 70, 80, 70, 80, 80)

        self._hist_tree = ttk.Treeview(
            table_frame, columns=cols, show="headings",
            style="GM.Treeview",
        )
        for col, lbl, w in zip(cols, col_labels, col_widths):
            self._hist_tree.heading(col, text=lbl)
            self._hist_tree.column(col, width=w, anchor="center")

        sb3 = ttk.Scrollbar(table_frame, orient="vertical", command=self._hist_tree.yview)
        self._hist_tree.configure(yscrollcommand=sb3.set)
        sb3.pack(side="right", fill="y", pady=8)
        self._hist_tree.pack(fill="both", expand=True, padx=8, pady=8)

    def _refresh_history_panel(self):
        if not hasattr(self, "_hist_tree"):
            return
        for row in self._hist_tree.get_children():
            self._hist_tree.delete(row)
        for rec in self.stats_mgr.history[:200]:
            self._hist_tree.insert("", "end", values=(
                rec.get("date", ""),
                rec.get("player", ""),
                rec.get("difficulty", ""),
                rec.get("mode", ""),
                rec.get("target", ""),
                rec.get("attempts", ""),
                rec.get("result", ""),
                rec.get("score", ""),
                rec.get("duration", ""),
            ))

    # ─────────────────────────────────────────
    # ACHIEVEMENTS VIEW
    # ─────────────────────────────────────────

    def _build_achievements_view(self):
        view = tk.Frame(self._content, bg=COLORS["bg_deep"])
        self._views["achievements"] = view

        hdr = tk.Frame(view, bg=COLORS["bg_panel"])
        hdr.pack(fill="x")
        tk.Label(hdr, text="🎖  Achievements",
                 font=FONTS["heading"], fg=COLORS["text_primary"],
                 bg=COLORS["bg_panel"], pady=16).pack(side="left", padx=24)

        self._ach_grid_outer = tk.Frame(view, bg=COLORS["bg_deep"])
        self._ach_grid_outer.pack(fill="both", expand=True, padx=24, pady=16)

    def _refresh_achievements(self):
        for w in self._ach_grid_outer.winfo_children():
            w.destroy()

        all_ach = self.ach_mgr.all_achievements()
        unlocked_count = sum(1 for a in all_ach if a["unlocked"])
        total = len(all_ach)

        tk.Label(self._ach_grid_outer,
                 text=f"{unlocked_count} / {total} Unlocked",
                 font=FONTS["subhead"],
                 fg=COLORS["accent"], bg=COLORS["bg_deep"]).pack(anchor="w", pady=(0, 12))

        grid = tk.Frame(self._ach_grid_outer, bg=COLORS["bg_deep"])
        grid.pack(fill="both", expand=True)

        cols = 4
        for i, data in enumerate(all_ach):
            badge = AchievementBadge(grid, data)
            badge.grid(row=i // cols, column=i % cols, padx=8, pady=8, sticky="nsew")
        for c in range(cols):
            grid.columnconfigure(c, weight=1)

    # ─────────────────────────────────────────
    # SETTINGS VIEW
    # ─────────────────────────────────────────

    def _build_settings_view(self):
        view = tk.Frame(self._content, bg=COLORS["bg_deep"])
        self._views["settings"] = view

        hdr = tk.Frame(view, bg=COLORS["bg_panel"])
        hdr.pack(fill="x")
        tk.Label(hdr, text="⚙  Settings",
                 font=FONTS["heading"], fg=COLORS["text_primary"],
                 bg=COLORS["bg_panel"], pady=16).pack(side="left", padx=24)

        body = tk.Frame(view, bg=COLORS["bg_deep"])
        body.pack(fill="both", expand=True, padx=40, pady=24)

        def section(text):
            tk.Label(body, text=text, font=FONTS["subhead"],
                     fg=COLORS["text_secondary"], bg=COLORS["bg_deep"]).pack(anchor="w", pady=(16, 4))
            tk.Frame(body, bg=COLORS["border"], height=1).pack(fill="x", pady=(0, 8))

        section("Preferences")

        sound_row = tk.Frame(body, bg=COLORS["bg_deep"])
        sound_row.pack(anchor="w", pady=4)
        tk.Label(sound_row, text="Sound Effects",
                 font=FONTS["body"], fg=COLORS["text_primary"],
                 bg=COLORS["bg_deep"], width=20, anchor="w").pack(side="left")
        tk.Checkbutton(
            sound_row, variable=self._sound_on,
            text="Enabled",
            font=FONTS["small"],
            fg=COLORS["text_secondary"],
            bg=COLORS["bg_deep"],
            selectcolor=COLORS["bg_card"],
            activebackground=COLORS["bg_deep"],
            activeforeground=COLORS["accent"],
            cursor="hand2",
        ).pack(side="left")

        section("Data Management")

        reset_row = tk.Frame(body, bg=COLORS["bg_deep"])
        reset_row.pack(anchor="w", pady=4)

        accent_button(reset_row, "Reset Statistics", self._reset_stats,
                      width=20, color=COLORS["too_high"]).pack(side="left", padx=(0, 12))
        accent_button(reset_row, "Reset Leaderboard", self._reset_leaderboard,
                      width=20, color=COLORS["too_high"]).pack(side="left", padx=(0, 12))
        accent_button(reset_row, "Reset Achievements", self._reset_achievements,
                      width=20, color=COLORS["too_high"]).pack(side="left")

        section("About")
        about_text = (
            "GuessMaster Pro  v1.0.0\n"
            "Built with Python 3 · Tkinter · OOP Architecture\n"
            "Internship Project — Prodigy InfoTech  ·  Task 02\n"
            "GitHub: github.com/your-username/GuessMaster-Pro"
        )
        tk.Label(body, text=about_text, font=FONTS["body"],
                 fg=COLORS["text_secondary"], bg=COLORS["bg_deep"],
                 justify="left").pack(anchor="w", pady=4)

    # ─────────────────────────────────────────
    # GAME LOGIC (connected to UI)
    # ─────────────────────────────────────────

    def _start_game(self):
        # Cancel any running timer
        if self._timer_job:
            self.after_cancel(self._timer_job)
            self._timer_job = None

        diff = Difficulty.from_label(self._difficulty.get())
        mode = GameMode(self._mode.get())
        name = self._player_name.get().strip() or "Player"

        self.engine.new_game(name, diff, mode)

        # Clear inline history
        for w in self._guess_hist_frame.winfo_children():
            w.destroy()

        # Update labels
        self._lbl_range.config(
            text=f"Guess the number  ·  {diff.range_label}",
            fg=COLORS["text_primary"],
        )
        self._lbl_difficulty.config(text=f"  {diff.label}  ")
        self._lbl_mode.config(text=f"  {mode.value}  ")
        self._lbl_feedback.config(text="Make your first guess!", fg=COLORS["text_secondary"])
        self._lbl_error.config(text="")
        self._set_progress(0, mode)
        self._guess_var.set("")

        # Enable input
        self._entry.config(state="normal")
        self._btn_guess.config(state="normal")
        self._entry.focus_set()

        # Sidebar stats
        self._sc_attempts.update_value("0")
        if mode == GameMode.CHALLENGE:
            self._sc_remaining.update_value(str(diff.max_attempts))
        else:
            self._sc_remaining.update_value("∞")

        self._refresh_stats_panel()

        # Start timer if Time Attack
        if mode == GameMode.TIME_ATTACK:
            self._tick_timer()
        else:
            self._lbl_timer.config(text="")

    def _set_progress(self, pct: float, mode: GameMode,
                      attempts_used: int = 0, max_attempts: Optional[int] = None):
        """Update the progress bar value and its descriptive labels."""
        pct = max(0, min(100, pct))
        self._progress_var.set(pct)
        self._lbl_progress_value.config(fg=COLORS["accent"])

        if mode == GameMode.CHALLENGE and max_attempts:
            self._lbl_progress_title.config(text="Attempts Used")
            self._lbl_progress_value.config(text=f"{attempts_used} / {max_attempts}")
        else:
            self._lbl_progress_title.config(text="Range Narrowed")
            self._lbl_progress_value.config(text=f"{int(pct)}%")

    def _tick_timer(self):
        s = self.engine.session
        if s is None or not s.active:
            return

        remaining = s.time_remaining or 0
        if remaining <= 0:
            self._lbl_timer.config(text="⏱ 0:00", fg=COLORS["too_high"])
            self._handle_loss("Time's up! The number was")
            return

        mins = int(remaining) // 60
        secs = int(remaining) % 60
        color = COLORS["too_high"] if remaining < 10 else (
            COLORS["accent4"] if remaining < 20 else COLORS["accent2"]
        )
        self._lbl_timer.config(text=f"⏱ {mins}:{secs:02d}", fg=color)
        self._timer_job = self.after(500, self._tick_timer)

    def _submit_guess(self):
        s = self.engine.session
        if s is None or not s.active:
            return

        raw = self._guess_var.get()
        valid, value, err = self.engine.validate_guess(raw)
        if not valid:
            self._lbl_error.config(text=err)
            return
        self._lbl_error.config(text="")
        self._guess_var.set("")

        result = self.engine.make_guess(value)

        # Add row to inline history
        GuessRow(self._guess_hist_frame, result)
        self._guess_canvas.yview_moveto(1.0)

        # Update sidebar stats
        self._sc_attempts.update_value(str(s.attempts_used))
        if s.max_attempts is not None:
            rem = s.attempts_remaining or 0
            self._sc_remaining.update_value(str(rem))

        # Progress bar: attempts / max (or % of range converged)
        if s.max_attempts:
            pct = s.attempts_used / s.max_attempts * 100
        else:
            # Show convergence: how much range has been eliminated
            pct = min(100, (1 - result.distance / s.difficulty.max_val) * 100)
        self._set_progress(pct, s.mode, attempts_used=s.attempts_used, max_attempts=s.max_attempts)

        if result.is_correct:
            self._handle_win(result)
        else:
            # Feedback
            color = COLORS["too_high"] if result.direction == "high" else COLORS["too_low"]
            self._lbl_feedback.config(text=result.hint, fg=color)

            # Check loss
            if not s.active:
                self._handle_loss("No attempts left! The number was")

    def _handle_win(self, result: GuessResult):
        s = self.engine.session
        self._disable_input()

        self._lbl_feedback.config(
            text=f"🎉  Correct!  The number was {s.target}  ·  {s.attempts_used} attempt(s)",
            fg=COLORS["correct"],
        )
        self._lbl_progress_title.config(text="Solved")
        self._progress_var.set(100)
        self._lbl_progress_value.config(text="100%", fg=COLORS["correct"])

        # Persist
        self.stats_mgr.record_session(s)
        made_lb, rank = self.lb_mgr.submit(s)

        # Achievements
        new_ach = self.engine.check_achievements(
            self.stats_mgr.stats, self.stats_mgr.current_streak
        )
        newly_unlocked = self.ach_mgr.unlock_batch(new_ach)

        self._refresh_stats_panel()
        self._refresh_leaderboard()
        self._refresh_achievements()

        # Toast
        msg_parts = [f"🎯  Score: {s.score:,}"]
        if made_lb:
            msg_parts.append(f"🏆  Leaderboard Rank #{rank}")
        for a in newly_unlocked:
            msg_parts.append(f"{a['icon']}  Achievement: {a['name']}")
        self._show_toast("  ·  ".join(msg_parts), COLORS["correct"])

    def _handle_loss(self, prefix: str):
        s = self.engine.session
        self._disable_input()

        self._lbl_feedback.config(
            text=f"💀  {prefix} {s.target}",
            fg=COLORS["too_high"],
        )
        self.stats_mgr.record_session(s)
        self._refresh_stats_panel()
        self._show_toast(f"Game over — the number was {s.target}", COLORS["too_high"])

    def _disable_input(self):
        if self._timer_job:
            self.after_cancel(self._timer_job)
            self._timer_job = None
        self._entry.config(state="disabled")
        self._btn_guess.config(state="disabled")

    # ─────────────────────────────────────────
    # Stats refresh
    # ─────────────────────────────────────────

    def _refresh_stats_panel(self):
        st = self.stats_mgr.stats
        best  = st.get("best_score", 0)
        played = st.get("games_played", 0)
        avg   = self.stats_mgr.avg_attempts

        self._sc_best.update_value(f"{best:,}" if best else "—")
        self._sc_winrate.update_value(f"{self.stats_mgr.win_rate}%")
        self._sc_avg.update_value(str(avg) if avg else "—")
        self._sc_played.update_value(str(played))

    # ─────────────────────────────────────────
    # Toast notification
    # ─────────────────────────────────────────

    def _show_toast(self, message: str, color=None):
        color = color or COLORS["accent"]
        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.configure(bg=COLORS["bg_card"])

        tk.Label(toast, text=message, font=FONTS["body_b"],
                 fg=color, bg=COLORS["bg_card"],
                 padx=20, pady=12).pack()

        # Position bottom-center
        self.update_idletasks()
        tw = 600
        th = 48
        x = self.winfo_x() + (self.winfo_width() - tw) // 2
        y = self.winfo_y() + self.winfo_height() - th - 40
        toast.geometry(f"{tw}x{th}+{x}+{y}")

        toast.after(3000, toast.destroy)

    # ─────────────────────────────────────────
    # Achievement unlock popup
    # ─────────────────────────────────────────

    def _popup_achievement(self, ach: dict):
        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg=COLORS["bg_card"],
                        highlightthickness=2,
                        highlightbackground=COLORS["accent"])
        inner = tk.Frame(popup, bg=COLORS["bg_card"])
        inner.pack(padx=16, pady=12)

        tk.Label(inner, text="Achievement Unlocked!", font=FONTS["small_b"],
                 fg=COLORS["accent"], bg=COLORS["bg_card"]).pack()
        tk.Label(inner, text=f"{ach['icon']}  {ach['name']}", font=FONTS["body_b"],
                 fg=COLORS["text_primary"], bg=COLORS["bg_card"]).pack()
        tk.Label(inner, text=ach["desc"], font=FONTS["small"],
                 fg=COLORS["text_secondary"], bg=COLORS["bg_card"]).pack()

        self.update_idletasks()
        x = self.winfo_x() + self.winfo_width() - 280 - 20
        y = self.winfo_y() + 80
        popup.geometry(f"260x80+{x}+{y}")
        popup.after(3500, popup.destroy)

    # ─────────────────────────────────────────
    # Reset & Export
    # ─────────────────────────────────────────

    def _reset_stats(self):
        if messagebox.askyesno("Reset Statistics",
                               "Reset ALL statistics? This cannot be undone."):
            self.stats_mgr.reset()
            self._refresh_stats_panel()
            self._show_toast("Statistics reset.", COLORS["text_muted"])

    def _reset_leaderboard(self):
        if messagebox.askyesno("Reset Leaderboard",
                               "Clear the leaderboard? This cannot be undone."):
            self.lb_mgr.reset()
            self._refresh_leaderboard()
            self._show_toast("Leaderboard cleared.", COLORS["text_muted"])

    def _reset_achievements(self):
        if messagebox.askyesno("Reset Achievements",
                               "Clear all achievement progress? This cannot be undone."):
            self.ach_mgr.reset()
            self._refresh_achievements()
            self._show_toast("Achievements reset.", COLORS["text_muted"])

    def _export_history(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="guessmaster_history.csv",
        )
        if path:
            self.stats_mgr.export_history_csv(path)
            self._show_toast(f"History exported → {path}", COLORS["accent2"])

    def _export_leaderboard(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="guessmaster_leaderboard.csv",
        )
        if path:
            self.lb_mgr.export_csv(path)
            self._show_toast(f"Leaderboard exported → {path}", COLORS["accent2"])
