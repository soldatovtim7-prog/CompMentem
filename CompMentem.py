# ═══════════════════════════════════════════════════════════════════════════
#  COMPMENTEM v1.3
#  Менеджер терминальных команд — современный интерфейс
#
#  Лицензия: MIT
# ═══════════════════════════════════════════════════════════════════════════

import sys
import os
import json
import re
import platform
import subprocess
import shutil
import shlex
import stat
import time
import threading
import queue
import signal
import atexit
import logging

from pathlib import Path
from datetime import datetime
from collections import Counter

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font as tkfont

import customtkinter as ctk


# ═══════════════════════════════════════════════════════════════════════════
#  КОНФИГ
# ═══════════════════════════════════════════════════════════════════════════

APP_NAME = "CompMentem"
APP_VERSION = "1.3"
APP_AUTHOR = "luxmentis"

HOME = Path.home()
APP_DIR = HOME / ".command_keeper"
DATA_FILE = HOME / ".command_keeper.json"
BACKUP_FILE = HOME / ".command_keeper.backup.json"
SETTINGS_FILE = HOME / ".command_keeper.settings.json"
LOCK_FILE = APP_DIR / "app.lock"
RUNLOG_FILE = APP_DIR / "runlog.json"
LOG_FILE = APP_DIR / "app.log"

RUNNER_DIR = APP_DIR
RUNNER_FIFO = RUNNER_DIR / "input.fifo"
RUNNER_PID = RUNNER_DIR / "term.pid"
RUNNER_SH = RUNNER_DIR / "runner.sh"


# ═══════════════════════════════════════════════════════════════════════════
#  СЕТКА ОТСТУПОВ
# ═══════════════════════════════════════════════════════════════════════════

SP_XXS = 2
SP_XS = 4
SP_SM = 8
SP_MD = 12
SP_LG = 16
SP_XL = 24
SP_XXL = 32
SP_HUGE = 48

R_SM = 6
R_MD = 10
R_LG = 14
R_XL = 18

H_INPUT = 36
H_BUTTON = 36
H_ROW = 40
H_HEADER = 60
H_STATUS = 48


# ═══════════════════════════════════════════════════════════════════════════
#  ПАЛИТРА
#  Ключи:
#    SH   — POSIX shell (фиолетовый)
#    BASH — Linux/macOS shell (бирюзовый)
#    CMD  — Windows shell (серо-голубой)
# ═══════════════════════════════════════════════════════════════════════════

THEMES = {
    "Aurora": {
        "BG":          ("#f5f7fa", "#0d151f"),
        "SURFACE":     ("#ffffff", "#151f2b"),
        "SURFACE_2":   ("#f0f3f7", "#1a2533"),
        "SURFACE_3":   ("#e6ebf2", "#1f2b3c"),
        "INPUT":       ("#ffffff", "#111a24"),
        "HOVER":       ("#e6ebf2", "#1f2b3c"),
        "ACTIVE":      ("#d4dce8", "#2a3850"),

        "BORDER":      ("#d4dce8", "#1f2b3c"),
        "BORDER_SOFT": ("#e6ebf2", "#19222f"),
        "BORDER_HL":   ("#0097a7", "#4dd0e1"),

        "FG":          ("#1a2533", "#e0e8f0"),
        "FG_MUTED":    ("#5a6d82", "#8ba0b5"),
        "FG_DIM":      ("#8ba0b5", "#5a6d82"),
        "FG_BRIGHT":   ("#000000", "#ffffff"),

        "ACCENT":      ("#0097a7", "#4dd0e1"),
        "ACCENT_2":    ("#00838f", "#80deea"),
        "ACCENT_DEEP": ("#006064", "#0097a7"),
        "ACCENT_SOFT": ("#e0f4f7", "#1a3b45"),

        "WARNING":     ("#d68a00", "#ffb84d"),
        "SUCCESS":     ("#2e7d32", "#7cffb2"),
        "DANGER":      ("#c62828", "#ff7a8a"),
        "INFO":        ("#0277bd", "#7cdcff"),

        # Shells
        "SH":          ("#6a4c93", "#b09bff"),
        "BASH":        ("#0097a7", "#4dd0e1"),
        "CMD":         ("#455a64", "#90a4ae"),

        "FAVORITE":    ("#d68a00", "#ffb84d"),
        "PINNED":      ("#0097a7", "#4dd0e1"),

        "SHADOW_1":    ("#e0e6ee", "#070d15"),
        "SHADOW_2":    ("#eaf0f5", "#0a131c"),
        "SHADOW_3":    ("#f0f5f9", "#0f1a25"),

        "TERM_BG":     ("#1a2533", "#070d15"),
        "TERM_FG":     ("#e0e8f0", "#c8dce8"),
        "TERM_ERR":    ("#c62828", "#ff7a8a"),
        "TERM_OK":     ("#2e7d32", "#7cffb2"),
        "TERM_CMD":    ("#d68a00", "#ffb84d"),
        "TERM_DIM":    ("#5a6d82", "#5a6d82"),
        "TERM_INPUT":  ("#80deea", "#80deea"),
    },
    "Deep": {
        "BG":          ("#eef1f5", "#0a0f16"),
        "SURFACE":     ("#ffffff", "#111823"),
        "SURFACE_2":   ("#f0f3f7", "#161f2c"),
        "SURFACE_3":   ("#e6ebf2", "#1c2635"),
        "INPUT":       ("#ffffff", "#0d131c"),
        "HOVER":       ("#e6ebf2", "#1c2635"),
        "ACTIVE":      ("#d4dce8", "#26354a"),

        "BORDER":      ("#d4dce8", "#1c2635"),
        "BORDER_SOFT": ("#e6ebf2", "#141c28"),
        "BORDER_HL":   ("#0097a7", "#4dd0e1"),

        "FG":          ("#1a2533", "#dce6f0"),
        "FG_MUTED":    ("#5a6d82", "#7f94a8"),
        "FG_DIM":      ("#8ba0b5", "#52637a"),
        "FG_BRIGHT":   ("#000000", "#ffffff"),

        "ACCENT":      ("#0097a7", "#4dd0e1"),
        "ACCENT_2":    ("#00838f", "#80deea"),
        "ACCENT_DEEP": ("#006064", "#0097a7"),
        "ACCENT_SOFT": ("#e0f4f7", "#163540"),

        "WARNING":     ("#d68a00", "#e8b86f"),
        "SUCCESS":     ("#2e7d32", "#8ee8b8"),
        "DANGER":      ("#c62828", "#e88a9a"),
        "INFO":        ("#0277bd", "#6fc8e8"),

        "SH":          ("#6a4c93", "#b09bff"),
        "BASH":        ("#0097a7", "#4dd0e1"),
        "CMD":         ("#455a64", "#90a4ae"),

        "FAVORITE":    ("#d68a00", "#e8b86f"),
        "PINNED":      ("#0097a7", "#4dd0e1"),

        "SHADOW_1":    ("#e0e6ee", "#040810"),
        "SHADOW_2":    ("#eaf0f5", "#070b12"),
        "SHADOW_3":    ("#f0f5f9", "#0a0f18"),

        "TERM_BG":     ("#1a2533", "#040810"),
        "TERM_FG":     ("#e0e8f0", "#c8dce8"),
        "TERM_ERR":    ("#c62828", "#e88a9a"),
        "TERM_OK":     ("#2e7d32", "#8ee8b8"),
        "TERM_CMD":    ("#d68a00", "#e8b86f"),
        "TERM_DIM":    ("#5a6d82", "#52637a"),
        "TERM_INPUT":  ("#80deea", "#80deea"),
    },
    "Daylight": {
        "BG":          ("#f5f7fa", "#f5f7fa"),
        "SURFACE":     ("#ffffff", "#ffffff"),
        "SURFACE_2":   ("#f0f3f7", "#f0f3f7"),
        "SURFACE_3":   ("#e6ebf2", "#e6ebf2"),
        "INPUT":       ("#ffffff", "#ffffff"),
        "HOVER":       ("#e6ebf2", "#e6ebf2"),
        "ACTIVE":      ("#d4dce8", "#d4dce8"),

        "BORDER":      ("#d4dce8", "#d4dce8"),
        "BORDER_SOFT": ("#e6ebf2", "#e6ebf2"),
        "BORDER_HL":   ("#0097a7", "#0097a7"),

        "FG":          ("#1a2533", "#1a2533"),
        "FG_MUTED":    ("#5a6d82", "#5a6d82"),
        "FG_DIM":      ("#8ba0b5", "#8ba0b5"),
        "FG_BRIGHT":   ("#000000", "#000000"),

        "ACCENT":      ("#0097a7", "#0097a7"),
        "ACCENT_2":    ("#00838f", "#00838f"),
        "ACCENT_DEEP": ("#006064", "#006064"),
        "ACCENT_SOFT": ("#e0f4f7", "#e0f4f7"),

        "WARNING":     ("#d68a00", "#d68a00"),
        "SUCCESS":     ("#2e7d32", "#2e7d32"),
        "DANGER":      ("#c62828", "#c62828"),
        "INFO":        ("#0277bd", "#0277bd"),

        "SH":          ("#6a4c93", "#6a4c93"),
        "BASH":        ("#0097a7", "#0097a7"),
        "CMD":         ("#455a64", "#455a64"),

        "FAVORITE":    ("#d68a00", "#d68a00"),
        "PINNED":      ("#0097a7", "#0097a7"),

        "SHADOW_1":    ("#e0e6ee", "#e0e6ee"),
        "SHADOW_2":    ("#eaf0f5", "#eaf0f5"),
        "SHADOW_3":    ("#f0f5f9", "#f0f5f9"),

        "TERM_BG":     ("#1a2533", "#1a2533"),
        "TERM_FG":     ("#e0e8f0", "#e0e8f0"),
        "TERM_ERR":    ("#ff7a8a", "#ff7a8a"),
        "TERM_OK":     ("#7cffb2", "#7cffb2"),
        "TERM_CMD":    ("#ffb84d", "#ffb84d"),
        "TERM_DIM":    ("#5a6d82", "#5a6d82"),
        "TERM_INPUT":  ("#00838f", "#00838f"),
    },
}


# ═══════════════════════════════════════════════════════════════════════════
#  НАСТРОЙКИ ПО УМОЛЧАНИЮ
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_SETTINGS = {
    "theme": "Aurora",
    "appearance": "dark",
    "font_size": 11,
    "auto_copy": True,
    "confirm_delete": True,
    "sort_mode": "smart",
    "history_size": 50,
    "runlog_size": 200,
    "backup_on_save": True,

    "run_mode": "embedded",
    "term_shell": "auto",
    "term_font_size": 10,
    "term_max_lines": 5000,
    "terminal_prefer": "auto",
}


# ═══════════════════════════════════════════════════════════════════════════
#  ЛОГИРОВАНИЕ
# ═══════════════════════════════════════════════════════════════════════════

def _setup_logging():
    try:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8")],
        )
    except Exception:
        logging.basicConfig(level=logging.WARNING)


log = logging.getLogger("compmentem")


# ═══════════════════════════════════════════════════════════════════════════
#  ЛОК-ФАЙЛ
# ═══════════════════════════════════════════════════════════════════════════

def _is_pid_alive(pid):
    try:
        if platform.system() == "Windows":
            out = subprocess.check_output(
                ["tasklist", "/FI", f"PID eq {pid}"],
                text=True, errors="ignore")
            return str(pid) in out
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def acquire_lock():
    try:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        if LOCK_FILE.exists():
            try:
                pid = int(LOCK_FILE.read_text().strip())
                if _is_pid_alive(pid):
                    return False
            except Exception:
                pass
        LOCK_FILE.write_text(str(os.getpid()))
        atexit.register(
            lambda: LOCK_FILE.exists() and LOCK_FILE.unlink())
        return True
    except Exception:
        return True


# ═══════════════════════════════════════════════════════════════════════════
#  ХЕЛПЕРЫ ЦВЕТА
# ═══════════════════════════════════════════════════════════════════════════

def hex_to_rgb(h):
    try:
        h = h.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except Exception:
        return (0, 0, 0)


def rgb_to_hex(rgb):
    try:
        r, g, b = [max(0, min(255, int(x))) for x in rgb]
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return "#000000"


def blend(c1, c2, t):
    try:
        r1, g1, b1 = hex_to_rgb(c1)
        r2, g2, b2 = hex_to_rgb(c2)
        t = max(0.0, min(1.0, t))
        return rgb_to_hex((
            int(r1 + (r2 - r1) * t),
            int(g1 + (g2 - g1) * t),
            int(b1 + (b2 - b1) * t),
        ))
    except Exception:
        return c1


def dark(c):
    if isinstance(c, tuple) and len(c) == 2:
        return c[1]
    return c


def light(c):
    if isinstance(c, tuple) and len(c) == 2:
        return c[0]
    return c


# ═══════════════════════════════════════════════════════════════════════════
#  SHELL-ХЕЛПЕРЫ
# ═══════════════════════════════════════════════════════════════════════════

SHELL_ICONS = {
    "sh": "📜",
    "bash": "🐧",
    "cmd": "🪟",
}

SHELL_LABELS = {
    "sh": "📜 sh",
    "bash": "🐧 bash",
    "cmd": "🪟 cmd",
}

SHELL_COLORS = {
    "sh": "SH",
    "bash": "BASH",
    "cmd": "CMD",
}

SHELL_DESCRIPTIONS = {
    "sh": "POSIX-стандарт (Linux, macOS, BSD)",
    "bash": "Linux / macOS shell",
    "cmd": "Windows Command Prompt",
}

# Shells, работающие на текущей ОС
def _available_shells():
    """Список shell, доступных для запуска на текущей ОС."""
    if platform.system() == "Windows":
        return ("cmd",)
    return ("sh", "bash")


def is_shell_available(shell):
    """Можно ли запустить команду с этим shell на текущей ОС."""
    return shell in _available_shells()


def get_shell_icon(shell):
    return SHELL_ICONS.get(shell, "❓")


def get_shell_label(shell):
    return SHELL_LABELS.get(shell, shell.upper())


def get_shell_color_key(shell):
    return SHELL_COLORS.get(shell, "FG")


def get_shell_description(shell):
    return SHELL_DESCRIPTIONS.get(shell, "")


# ═══════════════════════════════════════════════════════════════════════════
#  SETTINGS
# ═══════════════════════════════════════════════════════════════════════════

class Settings:
    def __init__(self, path: Path):
        self.path = path
        self.data = self.load()

    def load(self):
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        return {**DEFAULT_SETTINGS, **loaded}
            except Exception as e:
                log.warning("Settings.load: %s", e)
        return dict(DEFAULT_SETTINGS)

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(self.path.suffix + ".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
        except Exception as e:
            log.warning("Settings.save: %s", e)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def update_many(self, mapping):
        self.data.update(mapping)
        self.save()


# ═══════════════════════════════════════════════════════════════════════════
#  PALETTE
# ═══════════════════════════════════════════════════════════════════════════

class Palette:
    _ui_family = None

    def __init__(self):
        self._settings = None
        self.name = "Aurora"
        self._apply_colors("Aurora")

    @classmethod
    def ensure_font_family(cls):
        if cls._ui_family is None:
            try:
                available = set(tkfont.families())
            except Exception:
                available = set()

            for name in ["Inter", "Inter Display", "SF Pro Display",
                          "Segoe UI Variable", "Segoe UI", "IBM Plex Sans",
                          "Ubuntu", "Noto Sans", "DejaVu Sans",
                          "Liberation Sans", "Arial"]:
                if name in available:
                    cls._ui_family = name
                    break
            else:
                cls._ui_family = "Sans Serif"
        return cls._ui_family

    def bind(self, settings):
        self._settings = settings
        self.apply(settings.get("theme", "Aurora"))

    def apply(self, name):
        self._apply_colors(name)

    def apply_partial(self, name):
        self._apply_colors(name)

    def _apply_colors(self, name):
        t = THEMES.get(name, THEMES["Aurora"])
        for k, v in t.items():
            setattr(self, k, v)
        self.name = name


# ═══════════════════════════════════════════════════════════════════════════
#  APP CONTEXT
# ═══════════════════════════════════════════════════════════════════════════

class AppContext:
    def __init__(self):
        self.settings = Settings(SETTINGS_FILE)
        self.palette = Palette()
        self.palette.bind(self.settings)

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings.set(key, value)

    def set_many(self, mapping):
        self.settings.update_many(mapping)


CTX = AppContext()
C = CTX.palette


# ═══════════════════════════════════════════════════════════════════════════
#  STORAGE
# ═══════════════════════════════════════════════════════════════════════════

class Storage:
    SAVE_DEBOUNCE_MS = 800

    def __init__(self, path: Path, ctx: AppContext):
        self.path = path
        self.ctx = ctx
        self.load_error = None
        self.data = self.load()
        self.history = self.data.get("history", [])
        self.runlog = self._load_runlog()
        self.dirty = False
        self._save_timer = None
        self._lock = threading.RLock()

    def _load_runlog(self):
        try:
            if RUNLOG_FILE.exists():
                with open(RUNLOG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        size = self.ctx.get("runlog_size", 200)
                        return data[-size:]
        except Exception as e:
            log.warning("runlog load: %s", e)
        return []

    def save_runlog(self):
        try:
            APP_DIR.mkdir(parents=True, exist_ok=True)
            size = self.ctx.get("runlog_size", 200)
            tmp = RUNLOG_FILE.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.runlog[-size:], f,
                          ensure_ascii=False, indent=2)
            os.replace(tmp, RUNLOG_FILE)
        except Exception as e:
            log.warning("runlog save: %s", e)

    def log_run(self, cmd, ok=True, note=""):
        self.runlog.append({
            "name": cmd.get("name", ""),
            "when": datetime.now().isoformat(),
            "ok": bool(ok),
            "note": note,
        })
        size = self.ctx.get("runlog_size", 200)
        if len(self.runlog) > size:
            self.runlog = self.runlog[-size:]
        self.save_runlog()

    def load(self):
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError("Ожидался объект JSON")
                data.setdefault("commands", [])
                data.setdefault("history", [])
                valid = [c for c in data["commands"]
                         if isinstance(c, dict)
                         and "name" in c and "text" in c]
                data["commands"] = valid
                return data
            except Exception as e:
                self.load_error = str(e)
                log.error("Storage.load: %s", e)
        return {"commands": [], "history": []}

    def mark_dirty(self):
        with self._lock:
            self.dirty = True
        self._schedule_save()

    def _schedule_save(self):
        if self._save_timer is not None:
            try:
                self._save_timer.cancel()
            except Exception:
                pass
        self._save_timer = threading.Timer(
            self.SAVE_DEBOUNCE_MS / 1000.0, self.save)
        self._save_timer.daemon = True
        self._save_timer.start()

    def save(self):
        with self._lock:
            if not self.dirty and self.path.exists():
                return
            try:
                if (self.ctx.get("backup_on_save")
                        and self.path.exists()):
                    try:
                        shutil.copy2(self.path, BACKUP_FILE)
                    except Exception as e:
                        log.warning("backup: %s", e)

                hist_size = self.ctx.get("history_size", 50)
                self.data["history"] = self.history[-hist_size:]

                tmp = self.path.with_suffix(self.path.suffix + ".tmp")
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
                os.replace(tmp, self.path)
                self.dirty = False
            except Exception as e:
                log.error("Storage.save: %s", e)

    def flush(self):
        if self._save_timer is not None:
            try:
                self._save_timer.cancel()
            except Exception:
                pass
            self._save_timer = None
        self.save()

    def add(self, cmd):
        cmd.setdefault("uses", 0)
        cmd.setdefault("created", datetime.now().isoformat())
        cmd.setdefault("pinned", False)
        cmd.setdefault("favorite", False)
        self.data["commands"].append(cmd)
        self.mark_dirty()

    def update(self, idx, cmd):
        if 0 <= idx < len(self.data["commands"]):
            self.data["commands"][idx] = cmd
            self.mark_dirty()

    def delete(self, idx):
        if 0 <= idx < len(self.data["commands"]):
            del self.data["commands"][idx]
            self.mark_dirty()

    def duplicate(self, idx):
        if not (0 <= idx < len(self.data["commands"])):
            return None
        cmd = dict(self.data["commands"][idx])
        cmd["name"] = cmd["name"] + " (копия)"
        cmd["created"] = datetime.now().isoformat()
        cmd["uses"] = 0
        cmd["pinned"] = False
        self.data["commands"].append(cmd)
        self.mark_dirty()
        return len(self.data["commands"]) - 1

    def all(self):
        return self.data["commands"]

    def add_history(self, action, name):
        self.history.append({
            "action": action,
            "name": name,
            "when": datetime.now().isoformat(),
        })
        size = self.ctx.get("history_size", 50)
        if len(self.history) > size:
            self.history = self.history[-size:]
        self.data["history"] = self.history

    def export(self, path):
        tmp = Path(str(path) + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)

    def import_(self, path, strategy="merge"):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("Ожидался объект JSON")
        incoming = data.get("commands", [])
        if not isinstance(incoming, list):
            raise ValueError("Поле commands должно быть списком")

        existing_by_key = {}
        for i, c in enumerate(self.data["commands"]):
            existing_by_key[(c.get("name"), c.get("text"))] = i

        added = replaced = skipped = 0
        for cmd in incoming:
            if (not isinstance(cmd, dict)
                    or "name" not in cmd or "text" not in cmd):
                skipped += 1
                continue
            key = (cmd.get("name"), cmd.get("text"))
            cmd.setdefault("uses", 0)
            cmd.setdefault("pinned", False)
            cmd.setdefault("favorite", False)
            cmd.setdefault("created", datetime.now().isoformat())

            if key in existing_by_key:
                if strategy == "replace":
                    self.data["commands"][existing_by_key[key]] = cmd
                    replaced += 1
                elif strategy == "merge":
                    old = self.data["commands"][existing_by_key[key]]
                    old["uses"] = max(old.get("uses", 0),
                                      cmd.get("uses", 0))
                    old["favorite"] = (old.get("favorite")
                                       or cmd.get("favorite"))
                    old["pinned"] = (old.get("pinned")
                                     or cmd.get("pinned"))
                    replaced += 1
                else:
                    skipped += 1
                continue
            self.data["commands"].append(cmd)
            existing_by_key[key] = len(self.data["commands"]) - 1
            added += 1

        self.mark_dirty()
        return added, replaced, skipped

    def categories(self):
        c = Counter()
        for cmd in self.data["commands"]:
            cat = (cmd.get("category") or "").strip()
            if cat:
                for tag in re.split(r"[,\s]+", cat):
                    if tag:
                        c[tag] += 1
        return c.most_common()

    def shell_counts(self):
        return {
            "sh": sum(1 for x in self.data["commands"]
                      if x.get("shell") == "sh"),
            "bash": sum(1 for x in self.data["commands"]
                        if x.get("shell") == "bash"),
            "cmd": sum(1 for x in self.data["commands"]
                       if x.get("shell") == "cmd"),
        }


# ═══ КОНЕЦ ЧАСТИ 1/3 ═══
# ═══ ЧАСТЬ 2/3 — CompMentem v1.3 ═══
#  TerminalRunner, EmbeddedConsole (улучшенный), виджеты
# ═══════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════
#  TERMINAL RUNNER
# ═══════════════════════════════════════════════════════════════════════════

class TerminalRunner:
    """
    Внешний терминал через FIFO (Linux) или cmd.exe (Windows).
    """

    FIFO_OPEN_TIMEOUT = 1.5

    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.process = None
        self.fifo_ready = False
        self._prepare_files()

    def _prepare_files(self):
        try:
            RUNNER_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        if platform.system() != "Windows":
            try:
                if RUNNER_FIFO.exists():
                    RUNNER_FIFO.unlink()
                os.mkfifo(RUNNER_FIFO, 0o600)
                self.fifo_ready = True
            except Exception as e:
                log.warning("mkfifo: %s", e)
                self.fifo_ready = False

            script = f"""#!/usr/bin/env bash
# CompMentem — внешний терминал
# Постоянный FIFO-цикл

cd "$HOME"

# ═══ Цвета ═══
NEON='\\033[1;38;5;80m'
YELLOW='\\033[1;38;5;220m'
GREEN='\\033[1;38;5;82m'
RED='\\033[1;38;5;203m'
DIM='\\033[2m'
RESET='\\033[0m'

clear

# ═══ Баннер ═══
echo ""
echo -e "  ${{NEON}}>_${{RESET}}  ${{YELLOW}}CompMentem${{RESET}} ${{DIM}}v1.3${{RESET}}"
echo -e "  ${{DIM}}Менеджер терминальных команд${{RESET}}"
echo ""
echo -e "  ${{DIM}}Команды из приложения CompMentem идут сюда.${{RESET}}"
echo -e "  ${{DIM}}Окно не закрывается при переключении команд.${{RESET}}"
echo ""
echo -e "  ${{DIM}}Рабочая папка: ${{YELLOW}}$HOME${{RESET}}"
echo ""
echo -e "  ${{DIM}}─────────────────────────────────────────────────────${{RESET}}"
echo ""

FIFO="{RUNNER_FIFO}"
COUNTER=0

while true; do
    if [ ! -p "$FIFO" ]; then sleep 1; continue; fi
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        COUNTER=$((COUNTER + 1))

        echo ""
        echo -e "${{NEON}}  ❯${{RESET}} ${{YELLOW}}$line${{RESET}}"
        echo ""
        eval "$line"
        EXIT=$?
        echo ""
        if [ $EXIT -eq 0 ]; then
            echo -e "${{GREEN}}  ✓${{RESET}} ${{DIM}}Готово (команда #$COUNTER)${{RESET}}"
        else
            echo -e "${{RED}}  ✗${{RESET}} ${{DIM}}Ошибка $EXIT (команда #$COUNTER)${{RESET}}"
        fi
        echo -e "${{DIM}}  ─────────────────────────────────────────────────────${{RESET}}"
    done < "$FIFO"
    sleep 0.5
done
"""
            try:
                RUNNER_SH.write_text(script, encoding="utf-8")
                os.chmod(RUNNER_SH,
                         os.stat(RUNNER_SH).st_mode | stat.S_IXUSR)
            except Exception as e:
                log.warning("runner.sh: %s", e)

    def _pick_terminal(self):
        prefer = self.ctx.get("terminal_prefer", "auto")
        if prefer and prefer != "auto" and shutil.which(prefer):
            return prefer
        for t in ("x-terminal-emulator", "gnome-terminal",
                  "konsole", "xfce4-terminal", "alacritty",
                  "kitty", "xterm", "mate-terminal",
                  "lxterminal", "tilix"):
            if shutil.which(t):
                return t
        return None

    def start(self, force=False):
        if self.is_running() and not force:
            return True

        if platform.system() == "Windows":
            try:
                self.process = subprocess.Popen(
                    ["cmd.exe", "/k", "title CompMentem"],
                    creationflags=subprocess.CREATE_NEW_CONSOLE)
                return True
            except Exception as e:
                log.error("start win: %s", e)
                return False

        term = self._pick_terminal()
        if not term:
            log.error("Терминал не найден")
            return False

        if not RUNNER_SH.exists():
            self._prepare_files()

        try:
            icon = "/usr/share/icons/hicolor/scalable/apps/compmentem.svg"
            if not os.path.exists(icon):
                icon = str(HOME / "Рабочий стол" / "compmentem_icon.svg")

            if term in ("gnome-terminal", "x-terminal-emulator"):
                args = [term, "--title=CompMentem",
                        "--geometry=140x40"]
                if os.path.exists(icon):
                    args.append(f"--icon={icon}")
                args.extend(["--", "bash", str(RUNNER_SH)])
            elif term in ("alacritty", "kitty"):
                args = [term, "-t", "CompMentem",
                        "-e", "bash", str(RUNNER_SH)]
            elif term == "konsole":
                args = [term, "-p", "tabtitle=CompMentem"]
                if os.path.exists(icon):
                    args.extend(["--icon", icon])
                args.extend(["-e", "bash", str(RUNNER_SH)])
            else:
                args = [term, "-T", "CompMentem",
                        "-e", f"bash {shlex.quote(str(RUNNER_SH))}"]

            log.info("Запуск терминала: %s", " ".join(args))
            self.process = subprocess.Popen(
                args, start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)

            try:
                RUNNER_PID.write_text(str(self.process.pid))
            except Exception:
                pass

            return True
        except Exception as e:
            log.error("start terminal: %s", e)
            self.process = None
            return False

    def is_running(self):
        return (self.process is not None
                and self.process.poll() is None)

    def _open_fifo_nonblocking(self, timeout=None):
        timeout = timeout or self.FIFO_OPEN_TIMEOUT
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                fd = os.open(str(RUNNER_FIFO),
                             os.O_WRONLY | os.O_NONBLOCK)
                return os.fdopen(fd, "w", encoding="utf-8")
            except OSError:
                time.sleep(0.05)
        return None

    def run(self, command: str, shell: str = "bash"):
        # ═══ Проверка shell на текущей ОС ═══
        if not is_shell_available(shell):
            if shell == "cmd":
                raise RuntimeError(
                    "🪟 CMD-команда — только для Windows")
            raise RuntimeError(f"Shell '{shell}' недоступен")

        if platform.system() == "Windows":
            try:
                subprocess.Popen(
                    ["cmd.exe", "/k", command],
                    creationflags=subprocess.CREATE_NEW_CONSOLE)
                return True
            except Exception as e:
                raise RuntimeError(f"Ошибка cmd: {e}")

        if not self.is_running():
            if not self.start():
                raise RuntimeError("Терминал не найден")
            time.sleep(0.3)

        if not (self.fifo_ready and RUNNER_FIFO.exists()):
            raise RuntimeError("FIFO недоступен")

        f = self._open_fifo_nonblocking()
        if f is None:
            raise RuntimeError("Читатель FIFO не отвечает")

        try:
            f.write(command.replace("\n", " && ") + "\n")
            f.flush()
        finally:
            try:
                f.close()
            except Exception:
                pass
        return True

    def stop(self):
        try:
            if self.process and self.process.poll() is None:
                self.process.terminate()
        except Exception:
            pass
        self.process = None

    def cleanup(self):
        self.stop()
        try:
            if RUNNER_FIFO.exists():
                RUNNER_FIFO.unlink()
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════
#  EMBEDDED CONSOLE (улучшенный)
# ═══════════════════════════════════════════════════════════════════════════

class EmbeddedConsole(ctk.CTkFrame):
    """
    Улучшенный встроенный терминал.

    Новое:
      - Постоянный промпт `CompMentem ❯`
      - Разделители между командами
      - Кнопки: очистить, копировать вывод, история
      - ПКМ → копировать всё
      - Меньше мусорных сообщений
    """

    PROMPT = "❯ "
    READ_CHUNK = 4096
    SEPARATOR = "─" * 55

    def __init__(self, parent, ctx, shell="auto", font_size=10):
        super().__init__(parent, fg_color=dark(C.SURFACE),
                         corner_radius=R_MD,
                         border_width=1,
                         border_color=dark(C.BORDER_SOFT))

        self.ctx = ctx
        self.shell = self._resolve_shell(shell)
        self.font_size = font_size
        self.proc = None
        self.reader_thread = None
        self._stop_reader = threading.Event()
        self._out_queue = queue.Queue()
        self._history = []
        self._history_pos = 0
        self._command_count = 0

        self._build_ui()
        self._start_shell()
        self.after(30, self._pump)

    def _resolve_shell(self, shell):
        if shell == "auto":
            return "bash"
        if shell not in ("sh", "bash"):
            return "bash"
        return shell

    # ─── UI ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ═══ Верхняя панель ═══
        bar = ctk.CTkFrame(self, fg_color=dark(C.SURFACE_2),
                           height=36, corner_radius=0)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        self.shell_badge = ctk.CTkLabel(
            bar, text=f" {self.shell.upper()} ",
            fg_color=dark(C.ACCENT),
            text_color=dark(C.BG),
            corner_radius=R_SM,
            font=ctk.CTkFont(size=10, weight="bold"))
        self.shell_badge.pack(side="left",
                              padx=(SP_SM, SP_XS), pady=SP_XS)

        self.status_dot = ctk.CTkLabel(
            bar, text="●",
            text_color=dark(C.SUCCESS),
            font=ctk.CTkFont(size=14))
        self.status_dot.pack(side="left", padx=(0, SP_XS))

        self.status_lbl = ctk.CTkLabel(
            bar, text="running",
            text_color=dark(C.FG_MUTED),
            font=ctk.CTkFont(size=10))
        self.status_lbl.pack(side="left")

        # Кнопки справа
        for icon, cmd, color in [
            ("📋", self._copy_all, C.NEON if hasattr(C, "NEON")
             else C.ACCENT),
            ("⟲", self.restart, C.ACCENT),
            ("⏹", self.stop, C.DANGER),
            ("⌫", self.clear, C.FG_MUTED),
        ]:
            btn = ctk.CTkButton(
                bar, text=icon,
                width=28, height=24,
                corner_radius=R_SM,
                fg_color=dark(C.SURFACE_3),
                hover_color=dark(C.ACCENT),
                text_color=dark(color),
                font=ctk.CTkFont(size=13),
                command=cmd)
            btn.pack(side="right", padx=2, pady=SP_XS)

        # ═══ Текстовое поле ═══
        self.text = ctk.CTkTextbox(
            self,
            fg_color=dark(C.TERM_BG),
            text_color=dark(C.TERM_FG),
            corner_radius=0,
            border_width=0,
            font=ctk.CTkFont(
                family=C.ensure_font_family(),
                size=self.font_size + 1))
        self.text.pack(fill="both", expand=True, padx=1, pady=0)
        self.text.configure(state="disabled")

        # ПКМ — копировать всё
        self.text.bind("<Button-3>", self._on_right_click)

        # Теги
        try:
            self.text.tag_config("cmd", foreground=dark(C.TERM_CMD))
            self.text.tag_config("err", foreground=dark(C.TERM_ERR))
            self.text.tag_config("ok", foreground=dark(C.TERM_OK))
            self.text.tag_config("dim", foreground=dark(C.TERM_DIM))
            self.text.tag_config("prompt", foreground=dark(C.ACCENT))
            self.text.tag_config("sep", foreground=dark(C.FG_DIM))
            self.text.tag_config("input", foreground=dark(C.TERM_INPUT))
        except Exception:
            pass

        # ═══ Строка ввода ═══
        input_bar = ctk.CTkFrame(self, fg_color=dark(C.SURFACE_2),
                                  height=36, corner_radius=0)
        input_bar.pack(fill="x", side="bottom")
        input_bar.pack_propagate(False)

        self.prompt_lbl = ctk.CTkLabel(
            input_bar, text="CompMentem ❯ ",
            text_color=dark(C.ACCENT),
            font=ctk.CTkFont(size=12, weight="bold"))
        self.prompt_lbl.pack(side="left", padx=(SP_MD, SP_XS))

        self.input_var = tk.StringVar()
        self.input_entry = ctk.CTkEntry(
            input_bar,
            textvariable=self.input_var,
            fg_color="transparent",
            border_width=0,
            text_color=dark(C.TERM_FG),
            placeholder_text="Введи команду...",
            placeholder_text_color=dark(C.FG_DIM),
            font=ctk.CTkFont(
                family=C.ensure_font_family(),
                size=self.font_size + 1))
        self.input_entry.pack(side="left", fill="both", expand=True,
                              padx=(0, SP_MD), pady=SP_XS)
        self.input_entry.bind("<Return>", self._on_enter)
        self.input_entry.bind("<Up>", self._on_up)
        self.input_entry.bind("<Down>", self._on_down)
        self.input_entry.bind("<Control-c>", self._on_ctrl_c)
        self.input_entry.bind("<Control-l>", lambda e: self.clear())

        # Приветствие
        self._write_banner()
        self.after(100, self._focus_input)

    def _write_banner(self):
        self._write(f"\n", "dim")
        self._write(f"  >_ CompMentem ", "prompt")
        self._write(f"v1.3\n", "dim")
        self._write(f"  Встроенный терминал: {self.shell}\n", "dim")
        self._write(f"  Enter — выполнить. ↑/↓ — история.\n", "dim")
        self._write(f"  Ctrl+C — прервать, Ctrl+L — очистить.\n", "dim")
        self._write(f"  ПКМ — копировать всё.\n\n", "dim")
        self._write(f"  {self.SEPARATOR}\n\n", "sep")

    # ─── PROCESS ───────────────────────────────────────────────────────────
    def _start_shell(self):
        try:
            env = {**os.environ, "PS1": "", "TERM": "dumb",
                   "LC_ALL": "C.UTF-8"}
            shell_bin = "bash" if self.shell == "bash" else "sh"
            self.proc = subprocess.Popen(
                [shell_bin, "--norc", "--noprofile", "-i", "+m"]
                if shell_bin == "bash"
                else [shell_bin, "-i"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0, shell=False,
                start_new_session=True, env=env)
        except Exception as e:
            self._write(f"[!] Не удалось запустить {self.shell}: {e}\n",
                        "err")
            log.error("EmbeddedConsole start: %s", e)
            self.proc = None
            return

        self._stop_reader.clear()
        self.reader_thread = threading.Thread(
            target=self._reader_loop, daemon=True)
        self.reader_thread.start()

    def _reader_loop(self):
        if not self.proc or not self.proc.stdout:
            return
        fd = self.proc.stdout.fileno()
        try:
            os.set_blocking(fd, False)
        except Exception:
            pass

        while not self._stop_reader.is_set():
            try:
                chunk = os.read(fd, self.READ_CHUNK)
            except (BlockingIOError, InterruptedError):
                time.sleep(0.03)
                if self.proc.poll() is not None:
                    try:
                        chunk = os.read(fd, self.READ_CHUNK)
                    except Exception:
                        chunk = b""
                    if not chunk:
                        break
                continue
            except OSError:
                break
            if not chunk:
                break
            text = chunk.decode("utf-8", errors="replace")
            self._out_queue.put(text)
        self._out_queue.put(None)

    # ─── EVENTS ────────────────────────────────────────────────────────────
    def _focus_input(self):
        try:
            self.input_entry.focus_set()
        except Exception:
            pass

    def _on_enter(self, _e=None):
        line = self.input_var.get()
        self.input_var.set("")
        if line.strip():
            self._history.append(line)
            self._history_pos = len(self._history)
        self.send(line)
        return "break"

    def _on_up(self, _e=None):
        if not self._history:
            return "break"
        self._history_pos = max(0, self._history_pos - 1)
        self.input_var.set(self._history[self._history_pos])
        return "break"

    def _on_down(self, _e=None):
        if not self._history:
            return "break"
        self._history_pos = min(len(self._history),
                                self._history_pos + 1)
        if self._history_pos == len(self._history):
            self.input_var.set("")
        else:
            self.input_var.set(self._history[self._history_pos])
        return "break"

    def _on_ctrl_c(self, _e=None):
        self.stop()
        return "break"

    def _on_right_click(self, _e=None):
        """ПКМ — меню: копировать всё."""
        try:
            menu = tk.Menu(self, tearoff=0,
                           bg=dark(C.SURFACE_2),
                           fg=dark(C.FG),
                           activebackground=dark(C.ACCENT),
                           activeforeground=dark(C.BG))
            menu.add_command(label="📋  Копировать всё",
                             command=self._copy_all)
            menu.add_command(label="🗑  Очистить",
                             command=self.clear)
            menu.tk_popup(_e.x_root, _e.y_root)
        except Exception as e:
            log.warning("right click menu: %s", e)

    # ─── PUBLIC ────────────────────────────────────────────────────────────
    def send(self, line: str):
        if not self.proc or self.proc.poll() is not None:
            self._write("[!] Процесс не запущен, перезапускаю...\n",
                        "dim")
            self._start_shell()
            if not self.proc:
                return

        self._command_count += 1
        self._write(f"\n  ❯ ", "prompt")
        self._write(f"{line}\n\n", "cmd")
        try:
            data = (line + "\n").encode("utf-8", errors="replace")
            self.proc.stdin.write(data)
            self.proc.stdin.flush()
        except Exception as e:
            self._write(f"\n[!] Ошибка записи: {e}\n", "err")

    def run_command(self, command: str):
        for line in command.splitlines() or [command]:
            self.send(line)

    def stop(self):
        if not self.proc or self.proc.poll() is not None:
            return
        try:
            self.proc.send_signal(signal.SIGINT)
            self._write("^C\n", "dim")
        except Exception as e:
            self._write(f"[!] Не удалось прервать: {e}\n", "err")

    def clear(self):
        try:
            self.text.configure(state="normal")
            self.text.delete("1.0", "end")
            self.text.configure(state="disabled")
            self._write_banner()
        except Exception:
            pass

    def restart(self):
        self.stop()
        try:
            if self.proc:
                try:
                    os.killpg(os.getpgid(self.proc.pid),
                              signal.SIGTERM)
                except Exception:
                    self.proc.terminate()
        except Exception:
            pass
        self._stop_reader.set()
        self._write("\n# Перезапуск...\n", "dim")
        self._start_shell()

    def set_shell(self, shell):
        target = self._resolve_shell(shell)
        if target == self.shell:
            return
        self.restart()
        self.shell = target
        self.shell_badge.configure(text=f" {self.shell.upper()} ")

    def shutdown(self):
        self._stop_reader.set()
        try:
            if self.proc:
                try:
                    os.killpg(os.getpgid(self.proc.pid),
                              signal.SIGTERM)
                except Exception:
                    self.proc.terminate()
        except Exception:
            pass

    def _copy_all(self):
        """Копировать весь текст терминала в буфер."""
        try:
            self.text.configure(state="normal")
            content = self.text.get("1.0", "end")
            self.text.configure(state="disabled")
            self.clipboard_clear()
            self.clipboard_append(content)
            self.update()
            Toast.show(self.winfo_toplevel(),
                       "Скопировано в буфер", C.SUCCESS, icon="📋")
        except Exception as e:
            log.warning("copy all: %s", e)

    # ─── INTERNAL ──────────────────────────────────────────────────────────
    def _write(self, text, tag=None):
        try:
            self.text.configure(state="normal")
            if tag:
                self.text.insert("end", text, tag)
            else:
                self.text.insert("end", text)
            self.text.configure(state="disabled")
            self.text.see("end")

            max_lines = self.ctx.get("term_max_lines", 5000)
            try:
                line_count = int(
                    self.text.index("end-1c").split(".")[0])
                if line_count > max_lines:
                    self.text.configure(state="normal")
                    self.text.delete("1.0",
                                     f"{line_count - max_lines}.0")
                    self.text.configure(state="disabled")
            except Exception:
                pass
        except Exception as e:
            log.warning("console write: %s", e)

    def _pump(self):
        try:
            drained = 0
            while drained < 300:
                try:
                    item = self._out_queue.get_nowait()
                except queue.Empty:
                    break
                if item is None:
                    self.status_dot.configure(
                        text_color=dark(C.DANGER))
                    self.status_lbl.configure(
                        text="stopped",
                        text_color=dark(C.DANGER))
                    self._write("\n# Процесс завершён.\n", "dim")
                    self.proc = None
                    break
                self._write(item)
                drained += 1
        except Exception as e:
            log.warning("pump: %s", e)
        self.after(30, self._pump)


# ═══════════════════════════════════════════════════════════════════════════
#  ВИДЖЕТЫ
# ═══════════════════════════════════════════════════════════════════════════

class PillButton(ctk.CTkButton):
    """Капсула-тег."""

    def __init__(self, parent, text, color=None, command=None,
                 active=False, width=None, **kw):
        color = color or C.ACCENT
        self._color = color
        self._active = active

        super().__init__(
            parent,
            text=text,
            height=28,
            corner_radius=14,
            fg_color=dark(color) if active else dark(C.SURFACE_2),
            hover_color=dark(C.HOVER) if not active else dark(color),
            text_color=dark(C.BG) if active else dark(color),
            border_width=1,
            border_color=dark(color),
            font=ctk.CTkFont(
                size=11,
                weight="bold" if active else "normal"),
            command=command,
            **kw)

        if width:
            self.configure(width=width)

    def set_active(self, active: bool):
        self._active = active
        if active:
            self.configure(
                fg_color=dark(self._color),
                hover_color=dark(self._color),
                text_color=dark(C.BG),
                border_color=dark(self._color),
                font=ctk.CTkFont(size=11, weight="bold"))
        else:
            self.configure(
                fg_color=dark(C.SURFACE_2),
                hover_color=dark(C.HOVER),
                text_color=dark(self._color),
                border_color=dark(self._color),
                font=ctk.CTkFont(size=11))

    def is_active(self):
        return self._active


class IconButton(ctk.CTkButton):
    """Компактная иконка-кнопка."""

    def __init__(self, parent, icon, command=None,
                 color=None, size=32, bg=None, **kw):
        color = color or C.FG
        bg = bg or C.SURFACE

        super().__init__(
            parent,
            text=icon,
            width=size,
            height=size,
            corner_radius=R_SM,
            fg_color=bg,
            hover_color=dark(C.HOVER),
            text_color=dark(color),
            border_width=0,
            font=ctk.CTkFont(size=int(size * 0.5)),
            command=command,
            **kw)


class SearchBar(ctk.CTkFrame):
    """Поле поиска с иконкой."""

    def __init__(self, parent, textvariable=None,
                 placeholder="Поиск...", height=None, **kw):
        super().__init__(
            parent,
            fg_color=dark(C.INPUT),
            corner_radius=R_SM,
            border_width=1,
            border_color=dark(C.BORDER_SOFT),
            height=height or H_INPUT,
            **kw)

        self.icon = ctk.CTkLabel(
            self,
            text="⌕",
            font=ctk.CTkFont(size=15),
            text_color=dark(C.FG_DIM),
            width=24)
        self.icon.pack(side="left", padx=(SP_SM, SP_XS))

        self.var = textvariable or tk.StringVar()
        self.entry = ctk.CTkEntry(
            self,
            textvariable=self.var,
            placeholder_text=placeholder,
            fg_color="transparent",
            border_width=0,
            text_color=dark(C.FG),
            placeholder_text_color=dark(C.FG_DIM),
            font=ctk.CTkFont(size=12))
        self.entry.pack(side="left", fill="both", expand=True,
                        padx=(0, SP_MD), pady=SP_XS)

        self.entry.bind("<FocusIn>", self._focus_in, add="+")
        self.entry.bind("<FocusOut>", self._focus_out, add="+")

    def _focus_in(self, _e):
        self.configure(border_color=dark(C.ACCENT))
        self.icon.configure(text_color=dark(C.ACCENT))

    def _focus_out(self, _e):
        self.configure(border_color=dark(C.BORDER_SOFT))
        self.icon.configure(text_color=dark(C.FG_DIM))

    def get(self):
        return self.var.get()

    def clear(self):
        self.var.set("")

    def focus(self):
        try:
            self.entry.focus_set()
        except Exception:
            pass


class Badge(ctk.CTkFrame):
    """Компактный бейдж."""

    def __init__(self, parent, text="", color=None, icon=None):
        color = color or C.ACCENT
        super().__init__(parent, fg_color=dark(C.SURFACE_3),
                         corner_radius=R_SM, height=24)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(padx=SP_SM, pady=2)

        self._color = color
        self.icon_lbl = None
        if icon:
            self.icon_lbl = ctk.CTkLabel(
                inner, text=icon,
                font=ctk.CTkFont(size=11),
                text_color=dark(color), width=14)
            self.icon_lbl.pack(side="left", padx=(0, SP_XS))

        self.text_lbl = ctk.CTkLabel(
            inner, text=text,
            font=ctk.CTkFont(size=11),
            text_color=dark(color))
        self.text_lbl.pack(side="left")

    def set_text(self, text):
        try:
            self.text_lbl.configure(text=text)
        except Exception:
            pass


class Toast(ctk.CTkToplevel):
    """Всплывающее уведомление."""

    _current = None

    @classmethod
    def show(cls, parent, text, color=None, duration=2400, icon="●"):
        try:
            if cls._current and cls._current.winfo_exists():
                cls._current.destroy()
        except Exception:
            pass
        cls._current = Toast(parent, text, color or C.ACCENT,
                             duration, icon)

    def __init__(self, parent, text, color, duration, icon):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        try:
            self.attributes("-alpha", 0.0)
        except Exception:
            pass

        outer = ctk.CTkFrame(self, fg_color=dark(color),
                             corner_radius=R_MD)
        outer.pack(fill="both", expand=True)
        inner = ctk.CTkFrame(outer, fg_color=dark(C.SURFACE_2),
                             corner_radius=R_MD - 2)
        inner.pack(fill="both", expand=True, padx=2, pady=2)

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(padx=SP_LG, pady=SP_MD)

        ctk.CTkLabel(row, text=icon,
                     font=ctk.CTkFont(size=16),
                     text_color=dark(color),
                     width=20).pack(side="left", padx=(0, SP_MD))
        ctk.CTkLabel(row, text=text,
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=dark(C.FG_BRIGHT)).pack(side="left")

        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()

        try:
            if parent and parent.winfo_exists():
                parent.update_idletasks()
                self._final_x = (parent.winfo_rootx()
                                 + parent.winfo_width()
                                 - w - SP_XXL)
                self._final_y = (parent.winfo_rooty()
                                 + parent.winfo_height()
                                 - h - SP_XXL)
            else:
                self._final_x = SP_XXL
                self._final_y = SP_XXL
        except Exception:
            self._final_x = SP_XXL
            self._final_y = SP_XXL

        self._final_x = max(0, self._final_x)
        self._final_y = max(0, self._final_y)
        self.geometry(f"+{self._final_x}+{self._final_y}")

        self._duration = duration
        self._fade_in()

    def _fade_in(self):
        try:
            a = self.attributes("-alpha")
            if a < 0.97:
                a = min(0.97, a + 0.14)
                self.attributes("-alpha", a)
                self.after(18, self._fade_in)
            else:
                self.after(self._duration, self._fade_out)
        except Exception:
            self.after(self._duration, self._fade_out)

    def _fade_out(self):
        try:
            a = self.attributes("-alpha")
            if a > 0.1:
                self.attributes("-alpha", a - 0.14)
                self.after(24, self._fade_out)
            else:
                self.destroy()
        except Exception:
            try:
                self.destroy()
            except Exception:
                pass


class ContextMenu(ctk.CTkToplevel):
    """Кастомное контекстное меню."""

    def __init__(self, parent, items, x, y):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        try:
            self.attributes("-alpha", 0.0)
        except Exception:
            pass

        self._root_bind_id = None
        self._root_widget = None

        outer = ctk.CTkFrame(self, fg_color=dark(C.BORDER_SOFT),
                             corner_radius=R_MD)
        outer.pack(fill="both", expand=True, padx=2, pady=2)
        inner = ctk.CTkFrame(outer, fg_color=dark(C.SURFACE_2),
                             corner_radius=R_MD - 2)
        inner.pack(fill="both", expand=True, padx=2, pady=2)

        for item in items:
            if item == "---":
                sep = ctk.CTkFrame(inner, fg_color="transparent",
                                    height=SP_SM)
                sep.pack(fill="x")
                sep.pack_propagate(False)
                tk.Frame(sep, bg=dark(C.BORDER_SOFT),
                         height=1).pack(fill="x", padx=SP_MD,
                                        pady=SP_XS)
                continue

            icon, label, hotkey, cb = item

            row = ctk.CTkFrame(inner, fg_color="transparent",
                                height=32, cursor="hand2")
            row.pack(fill="x", padx=SP_XS, pady=1)
            row.pack_propagate(False)

            ic = ctk.CTkLabel(row, text=icon,
                              font=ctk.CTkFont(size=13),
                              text_color=dark(C.ACCENT), width=24)
            ic.pack(side="left", padx=(SP_SM, SP_XS))

            tx = ctk.CTkLabel(row, text=label,
                              font=ctk.CTkFont(size=12),
                              text_color=dark(C.FG), anchor="w")
            tx.pack(side="left", fill="x", expand=True)

            hk = ctk.CTkLabel(row, text=hotkey or "",
                              font=ctk.CTkFont(size=10),
                              text_color=dark(C.FG_DIM))
            hk.pack(side="right", padx=(SP_SM, SP_LG))

            def on_enter(_e, r=row, i=ic, t=tx):
                try:
                    r.configure(fg_color=dark(C.HOVER))
                    t.configure(text_color=dark(C.ACCENT_2))
                    i.configure(text_color=dark(C.ACCENT_2))
                except Exception:
                    pass

            def on_leave(_e, r=row, i=ic, t=tx):
                try:
                    r.configure(fg_color="transparent")
                    t.configure(text_color=dark(C.FG))
                    i.configure(text_color=dark(C.ACCENT))
                except Exception:
                    pass

            def on_click(_e, c=cb):
                self.close()
                if c:
                    self.after(20, c)

            for w in (row, ic, tx, hk):
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)
                w.bind("<ButtonRelease-1>", on_click)

        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        if x + w > sw - SP_SM:
            x = sw - w - SP_SM
        if y + h > sh - SP_SM:
            y = sh - h - SP_SM
        if x < SP_SM:
            x = SP_SM
        if y < SP_SM:
            y = SP_SM
        self.geometry(f"+{x}+{y}")

        self.bind("<Escape>", lambda e: self.close())
        self.bind("<FocusOut>", lambda e: self.close())

        self._bind_outside()
        self.after(30, self._grab)
        self._fade_in()

    def _fade_in(self):
        try:
            a = self.attributes("-alpha")
            if a < 0.99:
                a = min(0.99, a + 0.16)
                self.attributes("-alpha", a)
                self.after(14, self._fade_in)
        except Exception:
            pass

    def _bind_outside(self):
        try:
            root = self.winfo_toplevel()
            self._root_widget = root
            self._root_bind_id = root.bind(
                "<ButtonRelease-1>", self._on_any_click, add="+")
        except Exception as e:
            log.warning("ctx bind: %s", e)

    def _on_any_click(self, event):
        try:
            x, y = self.winfo_rootx(), self.winfo_rooty()
            w, h = self.winfo_width(), self.winfo_height()
            if not (x <= event.x_root <= x + w
                    and y <= event.y_root <= y + h):
                self.close()
        except Exception:
            self.close()

    def _grab(self):
        try:
            self.focus_force()
        except Exception:
            pass

    def close(self):
        try:
            if self._root_widget and self._root_bind_id:
                self._root_widget.unbind("<ButtonRelease-1>",
                                         self._root_bind_id)
        except Exception:
            pass
        self._root_bind_id = None
        self._root_widget = None
        try:
            self.destroy()
        except Exception:
            pass


# ═══ КОНЕЦ ЧАСТИ 2/3 ═══
# ═══ ЧАСТЬ 3/3 — CompMentem v1.3 ═══
#  Диалоги + MainWindow + main()
# ═══════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════
#  BASE DIALOG
# ═══════════════════════════════════════════════════════════════════════════

class BaseDialog(ctk.CTkToplevel):
    """Каркас для всех диалогов."""

    def __init__(self, parent, title="", width=600, height=700):
        super().__init__(parent)
        self._parent = parent

        self.title(title)
        self.geometry(f"{width}x{height}")
        self.configure(fg_color=dark(C.BG))
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
        px = max(0, min(px, self.winfo_screenwidth() - width))
        py = max(0, min(py, self.winfo_screenheight() - height))
        self.geometry(f"{width}x{height}+{px}+{py}")

        self._build_header(title)

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True,
                          padx=SP_XL, pady=SP_LG)

        ctk.CTkFrame(self, fg_color=dark(C.BORDER_SOFT),
                     height=1).pack(fill="x", padx=SP_XL)

        self.footer = ctk.CTkFrame(self, fg_color="transparent")
        self.footer.pack(fill="x", padx=SP_XL, pady=(SP_MD, SP_LG))

        self.bind("<Escape>", lambda e: self._on_close())
        self.after(50, self._show)

    def _build_header(self, title):
        header = ctk.CTkFrame(self, fg_color="transparent",
                              height=60)
        header.pack(fill="x", padx=SP_XL, pady=(SP_LG, SP_SM))
        header.pack_propagate(False)

        ctk.CTkFrame(header, fg_color=dark(C.ACCENT),
                     width=3, height=24).pack(side="left",
                                                padx=(0, SP_MD))
        ctk.CTkLabel(
            header, text=title,
            font=ctk.CTkFont(
                family=C.ensure_font_family(),
                size=18, weight="bold"),
            text_color=dark(C.FG_BRIGHT),
            anchor="w").pack(side="left", fill="x", expand=True)

        ctk.CTkFrame(self, fg_color=dark(C.BORDER_SOFT),
                     height=1).pack(fill="x", padx=SP_XL)

    def _show(self):
        try:
            self.transient(self._parent)
            self.grab_set()
            self.focus_force()
            try:
                self.attributes("-alpha", 0.0)
            except Exception:
                return
            self._fade_step = 0
            self._fade_in()
        except Exception:
            pass

    def _fade_in(self):
        try:
            if self._fade_step >= 8:
                self.attributes("-alpha", 1.0)
                return
            a = (self._fade_step + 1) / 8
            self.attributes("-alpha", a)
            self._fade_step += 1
            self.after(15, self._fade_in)
        except Exception:
            pass

    def _on_close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    def add_footer_buttons(self, primary_text, primary_cmd,
                            secondary_text="Отмена",
                            secondary_cmd=None,
                            primary_icon=None):
        """Футер: [Отмена] [Основное].

        Если secondary_text пустой — вторая кнопка НЕ создаётся.
        """
        for w in self.footer.winfo_children():
            w.destroy()

        if secondary_text and secondary_text.strip():
            ctk.CTkButton(
                self.footer,
                text=secondary_text,
                width=120, height=H_BUTTON, corner_radius=R_SM,
                fg_color="transparent",
                hover_color=dark(C.HOVER),
                text_color=dark(C.FG),
                border_width=1,
                border_color=dark(C.BORDER_SOFT),
                font=ctk.CTkFont(size=12),
                command=secondary_cmd or self._on_close
            ).pack(side="right", padx=(SP_SM, 0))

        label = (f"{primary_icon}  {primary_text}"
                 if primary_icon else primary_text)
        ctk.CTkButton(
            self.footer,
            text=label,
            width=160, height=H_BUTTON, corner_radius=R_SM,
            fg_color=dark(C.ACCENT),
            hover_color=dark(C.ACCENT_2),
            text_color=dark(C.BG),
            font=ctk.CTkFont(size=12, weight="bold"),
            command=primary_cmd
        ).pack(side="right")


# ═══════════════════════════════════════════════════════════════════════════
#  COMMAND DIALOG (3 shell: sh / bash / cmd)
# ═══════════════════════════════════════════════════════════════════════════

class CommandDialog(BaseDialog):
    """Создание/редактирование команды. 3 shell: sh / bash / cmd."""

    def __init__(self, parent, ctx, title, command=None,
                 all_categories=None):
        self.ctx = ctx
        self.result = None

        command = command or {
            "name": "", "shell": "bash", "category": "",
            "text": "", "favorite": False, "pinned": False,
            "uses": 0}
        self._orig = command
        self._all_categories = all_categories or []

        super().__init__(parent, title=title.upper(),
                         width=640, height=820)

        self._build_content(command)
        self.add_footer_buttons(
            primary_text="Сохранить",
            primary_cmd=self._save,
            primary_icon="✓")

        self.bind("<Control-s>", lambda e: self._save())
        self.bind("<Control-Return>", lambda e: self._save())

    def _build_content(self, cmd):
        c = self.content

        # Название
        self._label(c, "Название")
        self.name_var = tk.StringVar(value=cmd["name"])
        self.name_entry = ctk.CTkEntry(
            c, textvariable=self.name_var,
            height=H_INPUT, corner_radius=R_SM,
            fg_color=dark(C.INPUT),
            border_color=dark(C.BORDER_SOFT),
            text_color=dark(C.FG))
        self.name_entry.pack(fill="x")

        # Shell + ★ + 📌
        mid = ctk.CTkFrame(c, fg_color="transparent")
        mid.pack(fill="x", pady=(SP_LG, 0))

        shell_col = ctk.CTkFrame(mid, fg_color="transparent")
        shell_col.pack(side="left", fill="x", expand=True)
        self._label(shell_col, "Оболочка")

        # ═══ 3 СЕГМЕНТА ═══
        self.shell_seg = ctk.CTkSegmentedButton(
            shell_col,
            values=["sh", "bash", "cmd"],
            height=H_INPUT,
            corner_radius=R_SM,
            fg_color=dark(C.SURFACE_2),
            selected_color=dark(C.ACCENT),
            selected_hover_color=dark(C.ACCENT_2),
            unselected_color=dark(C.SURFACE_2),
            unselected_hover_color=dark(C.HOVER),
            text_color=dark(C.FG),
            font=ctk.CTkFont(size=12),
            command=lambda v: self.after(
                30, self._fix_shell_seg_colors))
        active_shell = cmd["shell"]
        if active_shell not in ("sh", "bash", "cmd"):
            active_shell = "bash"
        self.shell_seg.set(active_shell)
        self.shell_seg.pack(anchor="w")
        self.after(50, self._fix_shell_seg_colors)

        # Подсказка про shell
        self.shell_hint = ctk.CTkLabel(
            shell_col, text="",
            font=ctk.CTkFont(size=10),
            text_color=dark(C.FG_DIM),
            anchor="w", justify="left")
        self.shell_hint.pack(fill="x", pady=(SP_XS, 0))
        self._update_shell_hint(active_shell)

        # ★
        fav_col = ctk.CTkFrame(mid, fg_color="transparent")
        fav_col.pack(side="right", padx=(SP_MD, 0))
        self._label(fav_col, "★")

        self._fav_active = bool(cmd.get("favorite", False))
        self.fav_btn = PillButton(
            fav_col,
            text="★ ДА" if self._fav_active else "☆ НЕТ",
            color=C.FAVORITE,
            active=self._fav_active,
            command=self._toggle_fav,
            width=80)
        self.fav_btn.pack(anchor="w", pady=(SP_XS, 0))

        # 📌
        pin_col = ctk.CTkFrame(mid, fg_color="transparent")
        pin_col.pack(side="right", padx=(SP_MD, 0))
        self._label(pin_col, "📌")

        self._pin_active = bool(cmd.get("pinned", False))
        self.pin_btn = PillButton(
            pin_col,
            text="📌 ДА" if self._pin_active else "📍 НЕТ",
            color=C.PINNED,
            active=self._pin_active,
            command=self._toggle_pin,
            width=80)
        self.pin_btn.pack(anchor="w", pady=(SP_XS, 0))

        # Категория
        self._label(c, "Категория / Теги")
        self.category_var = tk.StringVar(value=cmd["category"])
        ctk.CTkEntry(
            c, textvariable=self.category_var,
            height=H_INPUT, corner_radius=R_SM,
            fg_color=dark(C.INPUT),
            border_color=dark(C.BORDER_SOFT),
            text_color=dark(C.FG)).pack(fill="x")

        if self._all_categories:
            hint = ctk.CTkFrame(c, fg_color="transparent")
            hint.pack(fill="x", pady=(SP_SM, 0))
            ctk.CTkLabel(
                hint, text="Существующие:",
                font=ctk.CTkFont(size=10),
                text_color=dark(C.FG_DIM)).pack(side="left",
                                                  padx=(0, SP_SM))
            for cat in self._all_categories[:6]:
                pill = PillButton(
                    hint, text=f"#{cat}",
                    color=C.ACCENT,
                    command=lambda cc=cat: self._append_category(cc))
                pill.pack(side="left", padx=2)

        # Команда
        self._label(c, "Команда")
        text_wrap = ctk.CTkFrame(
            c, fg_color=dark(C.INPUT),
            corner_radius=R_SM, border_width=1,
            border_color=dark(C.BORDER_SOFT))
        text_wrap.pack(fill="both", expand=True)

        self.text_widget = ctk.CTkTextbox(
            text_wrap,
            fg_color="transparent",
            border_width=0,
            text_color=dark(C.ACCENT_2),
            font=ctk.CTkFont(
                family=C.ensure_font_family(),
                size=12))
        self.text_widget.pack(fill="both", expand=True,
                              padx=SP_SM, pady=SP_SM)
        self.text_widget.insert("1.0", cmd["text"])

    def _label(self, parent, text):
        ctk.CTkLabel(
            parent, text=text.upper(),
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=dark(C.FG_MUTED),
            anchor="w").pack(fill="x", pady=(SP_MD, SP_XS))

    def _update_shell_hint(self, shell):
        desc = get_shell_description(shell)
        available = is_shell_available(shell)
        if available:
            self.shell_hint.configure(
                text=f"  ✓ {desc}",
                text_color=dark(C.FG_DIM))
        else:
            self.shell_hint.configure(
                text=f"  ⚠ {desc} — не запустится на этой ОС",
                text_color=dark(C.WARNING))

    def _fix_shell_seg_colors(self):
        """Чёрный текст на активном сегменте."""
        try:
            seg = self.shell_seg
            active_val = seg.get()
            buttons = getattr(seg, "_buttons_dict", {})
            for val, btn in buttons.items():
                is_active = (val == active_val)
                color = dark(C.BG) if is_active else dark(C.FG)
                weight = "bold" if is_active else "normal"
                if hasattr(btn, "_text_label") and btn._text_label:
                    try:
                        btn._text_label.configure(
                            fg=color,
                            font=(C.ensure_font_family(),
                                  12, weight))
                    except Exception:
                        pass
                try:
                    btn.configure(
                        text_color=color,
                        font=ctk.CTkFont(size=12, weight=weight))
                except Exception:
                    pass
        except Exception as e:
            log.warning("_fix_shell_seg_colors: %s", e)
        # Обновляем подсказку
        try:
            self._update_shell_hint(self.shell_seg.get())
        except Exception:
            pass

    def _toggle_fav(self):
        self._fav_active = not self._fav_active
        self.fav_btn.configure(
            text="★ ДА" if self._fav_active else "☆ НЕТ")
        self.fav_btn.set_active(self._fav_active)

    def _toggle_pin(self):
        self._pin_active = not self._pin_active
        self.pin_btn.configure(
            text="📌 ДА" if self._pin_active else "📍 НЕТ")
        self.pin_btn.set_active(self._pin_active)

    def _append_category(self, cat):
        current = self.category_var.get().strip()
        parts = [p.strip()
                 for p in re.split(r"[,\s]+", current) if p.strip()]
        if cat not in parts:
            parts.append(cat)
        self.category_var.set(", ".join(parts))

    def _save(self):
        name = self.name_var.get().strip()
        text = self.text_widget.get("1.0", "end").strip()

        if not name:
            Toast.show(self._parent, "Укажи название",
                       C.DANGER, icon="⚠")
            self.name_entry.focus_set()
            return
        if not text:
            Toast.show(self._parent, "Укажи команду",
                       C.DANGER, icon="⚠")
            self.text_widget.focus_set()
            return

        self.result = {
            "name": name,
            "shell": self.shell_seg.get(),
            "category": self.category_var.get().strip(),
            "text": text,
            "favorite": self._fav_active,
            "pinned": self._pin_active,
            "uses": self._orig.get("uses", 0),
            "created": self._orig.get("created",
                                       datetime.now().isoformat()),
            "updated": datetime.now().isoformat(),
        }
        self._on_close()


# ═══════════════════════════════════════════════════════════════════════════
#  SETTINGS DIALOG
# ═══════════════════════════════════════════════════════════════════════════

class SettingsDialog(BaseDialog):
    """Настройки в 2 колонки."""

    def __init__(self, parent, ctx, on_apply):
        self.ctx = ctx
        self.on_apply = on_apply
        self._orig = {k: self.ctx.get(k)
                      for k in DEFAULT_SETTINGS.keys()}
        self._theme_btns = {}
        self._font_btns = {}

        super().__init__(parent, "Настройки", width=920, height=780)

        self._build_content()
        self.add_footer_buttons(
            primary_text="Применить",
            primary_cmd=self._apply,
            secondary_text="Отмена",
            secondary_cmd=self._cancel,
            primary_icon="✓")

        self.bind("<Control-s>", lambda e: self._apply())

    def _build_content(self):
        cols = ctk.CTkFrame(self.content, fg_color="transparent")
        cols.pack(fill="both", expand=True)

        left = ctk.CTkFrame(cols, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True,
                  padx=(0, SP_XL))
        right = ctk.CTkFrame(cols, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)

        # Тема
        self._section(left, "Тема")
        self.theme_var = tk.StringVar(value=self.ctx.get("theme"))
        for name in THEMES.keys():
            btn = ctk.CTkButton(
                left, text=f"  {name}  ",
                height=40, corner_radius=R_SM,
                fg_color=dark(C.SURFACE_2),
                hover_color=dark(C.HOVER),
                text_color=dark(C.FG),
                font=ctk.CTkFont(size=12),
                anchor="w",
                command=lambda n=name: self._set_theme(n))
            btn.pack(fill="x", pady=2)
            self._theme_btns[name] = btn
        self._refresh_themes()

        # Шрифт
        self._section(left, "Размер шрифта")
        self.font_var = tk.IntVar(value=self.ctx.get("font_size"))
        fs_row = ctk.CTkFrame(left, fg_color="transparent")
        fs_row.pack(fill="x")
        for size in (10, 11, 12, 13, 14, 16):
            btn = ctk.CTkButton(
                fs_row, text=str(size),
                width=46, height=34, corner_radius=R_SM,
                fg_color=dark(C.SURFACE_2),
                hover_color=dark(C.HOVER),
                text_color=dark(C.FG),
                font=ctk.CTkFont(size=11),
                command=lambda s=size: self._set_font(s))
            btn.pack(side="left", padx=(0, SP_XS))
            self._font_btns[size] = btn
        self._refresh_font()

        # Правая колонка
        self._section(right, "Куда запускать")
        self.run_mode = tk.StringVar(
            value=self.ctx.get("run_mode", "embedded"))
        for value, label in [
            ("embedded", "🖥  Встроенный (панель снизу)"),
            ("external", "🚀  Внешний (единое окно)"),
        ]:
            ctk.CTkRadioButton(
                right, text=label,
                variable=self.run_mode, value=value,
                fg_color=dark(C.ACCENT),
                hover_color=dark(C.ACCENT_2),
                text_color=dark(C.FG),
                font=ctk.CTkFont(size=12),
                radiobutton_width=20, radiobutton_height=20
            ).pack(anchor="w", pady=2)

        self._section(right, "Оболочка терминала")
        self.term_shell = tk.StringVar(
            value=self.ctx.get("term_shell", "auto"))
        for value, label in [
            ("auto", "Авто"),
            ("sh", "📜 sh"),
            ("bash", "🐧 bash"),
        ]:
            ctk.CTkRadioButton(
                right, text=label,
                variable=self.term_shell, value=value,
                fg_color=dark(C.ACCENT),
                hover_color=dark(C.ACCENT_2),
                text_color=dark(C.FG),
                font=ctk.CTkFont(size=12),
                radiobutton_width=20, radiobutton_height=20
            ).pack(anchor="w", pady=2)

        self._section(right, "Поведение")
        self.auto_copy = tk.BooleanVar(
            value=self.ctx.get("auto_copy", True))
        self.confirm_del = tk.BooleanVar(
            value=self.ctx.get("confirm_delete", True))
        self.backup = tk.BooleanVar(
            value=self.ctx.get("backup_on_save", True))

        for var, label in [
            (self.auto_copy, "Копировать при двойном клике"),
            (self.confirm_del, "Спрашивать при удалении"),
            (self.backup, "Бэкап при сохранении"),
        ]:
            ctk.CTkCheckBox(
                right, text=label,
                variable=var,
                fg_color=dark(C.ACCENT),
                hover_color=dark(C.ACCENT_2),
                text_color=dark(C.FG),
                font=ctk.CTkFont(size=12),
                checkbox_width=22, checkbox_height=22,
                border_width=2, corner_radius=6
            ).pack(anchor="w", pady=3)

        self._section(right, "Сортировка")
        self.sort_var = tk.StringVar(
            value=self.ctx.get("sort_mode", "smart"))
        for value, label in [
            ("smart", "Умная"),
            ("name", "Имя"),
            ("uses", "Частота использования"),
            ("favorite", "Избранное"),
        ]:
            ctk.CTkRadioButton(
                right, text=label,
                variable=self.sort_var, value=value,
                fg_color=dark(C.ACCENT),
                hover_color=dark(C.ACCENT_2),
                text_color=dark(C.FG),
                font=ctk.CTkFont(size=12),
                radiobutton_width=20, radiobutton_height=20
            ).pack(anchor="w", pady=2)

    def _section(self, parent, text):
        ctk.CTkFrame(parent, fg_color=dark(C.BORDER_SOFT),
                     height=1).pack(fill="x", pady=(SP_LG, SP_SM))
        ctk.CTkLabel(
            parent, text=text.upper(),
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=dark(C.FG_MUTED),
            anchor="w").pack(fill="x", pady=(0, SP_SM))

    def _set_theme(self, name):
        self.theme_var.set(name)
        C.apply_partial(name)
        self._refresh_themes()

    def _refresh_themes(self):
        active = self.theme_var.get()
        for n, btn in self._theme_btns.items():
            if n == active:
                btn.configure(fg_color=dark(C.ACCENT),
                              text_color=dark(C.BG),
                              font=ctk.CTkFont(size=12,
                                                weight="bold"))
            else:
                btn.configure(fg_color=dark(C.SURFACE_2),
                              text_color=dark(C.FG),
                              font=ctk.CTkFont(size=12))

    def _set_font(self, size):
        self.font_var.set(size)
        self._refresh_font()

    def _refresh_font(self):
        active = self.font_var.get()
        for s, btn in self._font_btns.items():
            if s == active:
                btn.configure(fg_color=dark(C.ACCENT),
                              text_color=dark(C.BG),
                              font=ctk.CTkFont(size=11,
                                                weight="bold"))
            else:
                btn.configure(fg_color=dark(C.SURFACE_2),
                              text_color=dark(C.FG),
                              font=ctk.CTkFont(size=11))

    def _cancel(self):
        try:
            self.ctx.set_many(self._orig)
            C.apply(self._orig.get("theme", "Aurora"))
        except Exception:
            pass
        self._on_close()

    def _apply(self):
        new_values = {
            "theme": self.theme_var.get(),
            "font_size": self.font_var.get(),
            "run_mode": self.run_mode.get(),
            "term_shell": self.term_shell.get(),
            "auto_copy": self.auto_copy.get(),
            "confirm_delete": self.confirm_del.get(),
            "backup_on_save": self.backup.get(),
            "sort_mode": self.sort_var.get(),
        }
        try:
            self.ctx.set_many(new_values)
        except Exception as e:
            messagebox.showerror("Настройки", f"{e}", parent=self)
            return
        self._on_close()
        if callable(self.on_apply):
            try:
                self.on_apply()
            except Exception as e:
                log.warning("apply: %s", e)


# ═══════════════════════════════════════════════════════════════════════════
#  STATS DIALOG (3 shell)
# ═══════════════════════════════════════════════════════════════════════════

class StatsDialog(BaseDialog):
    """Статистика с 3 shell."""

    def __init__(self, parent, storage):
        self.storage = storage
        super().__init__(parent, "Статистика", width=880, height=780)
        self._build_content()
        self.add_footer_buttons(
            primary_text="Закрыть",
            primary_cmd=self._on_close,
            secondary_text="",
            secondary_cmd=self._on_close)

    def _build_content(self):
        c = self.content
        cmds = self.storage.all()

        # Плитки
        self._section(c, "Общая статистика")
        tiles = ctk.CTkFrame(c, fg_color="transparent")
        tiles.pack(fill="x", pady=(0, SP_LG))

        stats = [
            ("Всего команд", len(cmds), C.ACCENT, "≡"),
            ("Избранных",
             sum(1 for x in cmds if x.get("favorite")),
             C.FAVORITE, "★"),
            ("Закреплённых",
             sum(1 for x in cmds if x.get("pinned")),
             C.PINNED, "📌"),
            ("Использований",
             sum(x.get("uses", 0) for x in cmds),
             C.WARNING, "🔥"),
            ("sh", sum(1 for x in cmds if x.get("shell") == "sh"),
             C.SH, "📜"),
            ("bash", sum(1 for x in cmds if x.get("shell") == "bash"),
             C.BASH, "🐧"),
        ]

        for i, (label, value, color, icon) in enumerate(stats):
            row, col = divmod(i, 3)
            tile = ctk.CTkFrame(
                tiles, fg_color=dark(C.SURFACE_2),
                corner_radius=R_MD, border_width=1,
                border_color=dark(C.BORDER_SOFT))
            tile.grid(row=row, column=col, padx=SP_XS, pady=SP_XS,
                      sticky="nsew")
            tiles.columnconfigure(col, weight=1)
            tiles.rowconfigure(row, weight=1)

            ctk.CTkFrame(tile, fg_color=dark(color),
                         height=3).pack(fill="x")
            inner = ctk.CTkFrame(tile, fg_color="transparent")
            inner.pack(fill="both", expand=True,
                       padx=SP_MD, pady=SP_MD)

            ctk.CTkLabel(
                inner, text=f"{icon}  {value}",
                font=ctk.CTkFont(size=26, weight="bold"),
                text_color=dark(color),
                anchor="w").pack(fill="x")
            ctk.CTkLabel(
                inner, text=label,
                font=ctk.CTkFont(size=10),
                text_color=dark(C.FG_MUTED),
                anchor="w").pack(fill="x")

        # Топ-10
        self._section(c, "Топ-10 по использованию")
        top = sorted(cmds, key=lambda x: -x.get("uses", 0))[:10]
        top_wrap = ctk.CTkFrame(
            c, fg_color=dark(C.SURFACE_2),
            corner_radius=R_MD, border_width=1,
            border_color=dark(C.BORDER_SOFT))
        top_wrap.pack(fill="x", pady=(0, SP_LG))

        if not top or top[0].get("uses", 0) == 0:
            ctk.CTkLabel(top_wrap, text="Нет данных",
                         font=ctk.CTkFont(size=12),
                         text_color=dark(C.FG_DIM)).pack(pady=SP_LG)
        else:
            max_uses = max(x.get("uses", 0) for x in top) or 1
            inner = ctk.CTkFrame(top_wrap, fg_color="transparent")
            inner.pack(fill="x", padx=SP_MD, pady=SP_MD)

            for i, cmd in enumerate(top, 1):
                row = ctk.CTkFrame(inner, fg_color="transparent")
                row.pack(fill="x", pady=3)

                ctk.CTkLabel(row, text=f"{i}.",
                             font=ctk.CTkFont(size=11),
                             text_color=dark(C.FG_DIM),
                             width=24, anchor="w").pack(side="left")

                name = cmd.get("name", "")
                if len(name) > 32:
                    name = name[:30] + "..."
                ctk.CTkLabel(row, text=name,
                             font=ctk.CTkFont(size=11),
                             text_color=dark(C.FG),
                             anchor="w",
                             width=280).pack(side="left")

                uses = cmd.get("uses", 0)
                prog = ctk.CTkProgressBar(
                    row, width=200, height=8, corner_radius=4,
                    fg_color=dark(C.SURFACE_3),
                    progress_color=dark(C.WARNING))
                prog.pack(side="left", padx=(SP_SM, SP_SM))
                prog.set(uses / max_uses)

                ctk.CTkLabel(row, text=f"🔥 {uses}",
                             font=ctk.CTkFont(size=11, weight="bold"),
                             text_color=dark(C.WARNING),
                             width=60,
                             anchor="e").pack(side="right")

        # Распределение по shell — 3 полосы
        self._section(c, "Распределение по shell")
        counts = self.storage.shell_counts()
        total = sum(counts.values()) or 1

        shell_wrap = ctk.CTkFrame(
            c, fg_color=dark(C.SURFACE_2),
            corner_radius=R_MD, border_width=1,
            border_color=dark(C.BORDER_SOFT))
        shell_wrap.pack(fill="x")
        shell_inner = ctk.CTkFrame(shell_wrap, fg_color="transparent")
        shell_inner.pack(fill="x", padx=SP_MD, pady=SP_MD)

        for shell_key, label, color in [
            ("sh", "📜  sh", C.SH),
            ("bash", "🐧  bash", C.BASH),
            ("cmd", "🪟  cmd", C.CMD),
        ]:
            count = counts.get(shell_key, 0)
            row = ctk.CTkFrame(shell_inner, fg_color="transparent")
            row.pack(fill="x", pady=(0, SP_SM))
            ctk.CTkLabel(row, text=label,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=dark(color),
                         width=100,
                         anchor="w").pack(side="left")

            prog = ctk.CTkProgressBar(
                row, height=10, corner_radius=5,
                fg_color=dark(C.SURFACE_3),
                progress_color=dark(color))
            prog.pack(side="left", fill="x", expand=True,
                      padx=(SP_SM, SP_SM))
            prog.set(count / total)

            ctk.CTkLabel(row,
                         text=f"{count}  ({int(count/total*100)}%)",
                         font=ctk.CTkFont(size=11),
                         text_color=dark(C.FG_MUTED),
                         width=100,
                         anchor="e").pack(side="right")

    def _section(self, parent, text):
        ctk.CTkFrame(parent, fg_color=dark(C.BORDER_SOFT),
                     height=1).pack(fill="x", pady=(SP_MD, SP_SM))
        ctk.CTkLabel(parent, text=text.upper(),
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=dark(C.FG_MUTED),
                     anchor="w").pack(fill="x", pady=(0, SP_SM))


# ═══════════════════════════════════════════════════════════════════════════
#  HISTORY DIALOG
# ═══════════════════════════════════════════════════════════════════════════

class HistoryDialog(BaseDialog):
    def __init__(self, parent, history):
        super().__init__(parent, "История действий",
                         width=760, height=580)
        self._build_content(history)
        self.add_footer_buttons(
            primary_text="Закрыть",
            primary_cmd=self._on_close,
            secondary_text="",
            secondary_cmd=self._on_close)

    def _build_content(self, history):
        c = self.content
        ctk.CTkLabel(c, text=f"Всего записей: {len(history)}",
                     font=ctk.CTkFont(size=11),
                     text_color=dark(C.FG_MUTED),
                     anchor="w").pack(fill="x", pady=(0, SP_MD))

        scroll = ctk.CTkScrollableFrame(
            c, fg_color=dark(C.SURFACE_2),
            corner_radius=R_MD,
            scrollbar_button_color=dark(C.SURFACE_3),
            scrollbar_button_hover_color=dark(C.ACCENT))
        scroll.pack(fill="both", expand=True)

        icons = {
            "copy": "📋", "run": "▶", "add": "➕", "edit": "✏",
            "delete": "🗑", "import": "⬇", "export": "⬆",
        }
        for h in reversed(history):
            try:
                when = datetime.fromisoformat(
                    h["when"]).strftime("%d.%m %H:%M:%S")
            except Exception:
                when = h.get("when", "")
            icon = icons.get(h.get("action", ""), "•")

            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", padx=SP_SM, pady=1)
            ctk.CTkLabel(row, text=icon,
                         font=ctk.CTkFont(size=13),
                         width=24).pack(side="left")
            ctk.CTkLabel(row, text=when,
                         font=ctk.CTkFont(size=10),
                         text_color=dark(C.FG_DIM),
                         width=100,
                         anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=h.get("name", ""),
                         font=ctk.CTkFont(size=11),
                         text_color=dark(C.FG),
                         anchor="w").pack(side="left", fill="x",
                                            expand=True)


# ═══════════════════════════════════════════════════════════════════════════
#  RUNLOG DIALOG
# ═══════════════════════════════════════════════════════════════════════════

class RunLogDialog(BaseDialog):
    def __init__(self, parent, runlog):
        super().__init__(parent, "Журнал запусков",
                         width=800, height=580)
        self._build_content(runlog)
        self.add_footer_buttons(
            primary_text="Закрыть",
            primary_cmd=self._on_close,
            secondary_text="",
            secondary_cmd=self._on_close)

    def _build_content(self, runlog):
        c = self.content
        ctk.CTkLabel(c, text=f"Всего записей: {len(runlog)}",
                     font=ctk.CTkFont(size=11),
                     text_color=dark(C.FG_MUTED),
                     anchor="w").pack(fill="x", pady=(0, SP_MD))

        scroll = ctk.CTkScrollableFrame(
            c, fg_color=dark(C.SURFACE_2),
            corner_radius=R_MD,
            scrollbar_button_color=dark(C.SURFACE_3),
            scrollbar_button_hover_color=dark(C.ACCENT))
        scroll.pack(fill="both", expand=True)

        for entry in reversed(runlog):
            try:
                when = datetime.fromisoformat(
                    entry["when"]).strftime("%d.%m %H:%M:%S")
            except Exception:
                when = entry.get("when", "")
            ok = entry.get("ok", True)
            icon = "✓" if ok else "✗"
            color = C.SUCCESS if ok else C.DANGER

            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", padx=SP_SM, pady=1)
            ctk.CTkLabel(row, text=icon,
                         font=ctk.CTkFont(size=13),
                         text_color=dark(color),
                         width=24).pack(side="left")
            ctk.CTkLabel(row, text=when,
                         font=ctk.CTkFont(size=10),
                         text_color=dark(C.FG_DIM),
                         width=100,
                         anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=entry.get("name", ""),
                         font=ctk.CTkFont(size=11),
                         text_color=dark(C.FG),
                         anchor="w").pack(side="left", fill="x",
                                            expand=True)


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════════════

class MainWindow(ctk.CTk):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx

        ctk.set_appearance_mode(ctx.get("appearance", "dark"))
        ctk.set_default_color_theme("dark-blue")

        self.title(f"{APP_NAME} {APP_VERSION}")
        self.geometry("1600x920")
        self.minsize(1100, 640)
        self.configure(fg_color=dark(C.BG))

        # Логика
        self.storage = Storage(DATA_FILE, ctx)
        self.runner = TerminalRunner(ctx)
        self.console = None
        self._console_visible = False

        # Состояние
        self.search_var = tk.StringVar()
        self.category_filter = tk.StringVar(value="")
        self.shell_filter = tk.StringVar(value="all")
        self.only_fav = False

        # Ссылки
        self._cat_buttons = {}
        self._fav_button = None
        self._search_bar = None
        self._shell_seg = None
        self._tree = None
        self._badge_count = None
        self._badge_fav = None
        self._badge_uses = None
        self._detail_name = None
        self._detail_meta = None
        self._detail_text = None
        self._shell_badge = None
        self._status_label = None
        self._list_count = None

        self._filtered = []

        self._setup_treeview_style()
        self._bind_hotkeys()
        self._build_ui()

        self.refresh()
        self._update_categories()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ─── STYLES ───
    def _setup_treeview_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Keeper.Treeview",
            background=dark(C.SURFACE),
            fieldbackground=dark(C.SURFACE),
            foreground=dark(C.FG),
            rowheight=H_ROW, borderwidth=0,
            font=(C.ensure_font_family(), 11, "normal"))
        style.configure(
            "Keeper.Treeview.Heading",
            background=dark(C.BG),
            foreground=dark(C.FG_MUTED),
            font=(C.ensure_font_family(), 10, "bold"),
            borderwidth=0, relief="flat",
            padding=(12, 8))
        style.map("Keeper.Treeview.Heading",
                  background=[("active", dark(C.HOVER))],
                  foreground=[("active", dark(C.ACCENT_2))])
        style.map("Keeper.Treeview",
                  background=[("selected", dark(C.ACCENT_SOFT))],
                  foreground=[("selected", dark(C.ACCENT_2))])
        style.configure(
            "Keeper.Vertical.TScrollbar",
            background=dark(C.SURFACE_3),
            troughcolor=dark(C.BG),
            bordercolor=dark(C.BG),
            arrowcolor=dark(C.FG_MUTED),
            darkcolor=dark(C.SURFACE_3),
            lightcolor=dark(C.SURFACE_3),
            relief="flat", arrowsize=10)
        style.map("Keeper.Vertical.TScrollbar",
                  background=[("active", dark(C.ACCENT))])

    # ─── UI ───
    def _build_ui(self):
        self._build_header()
        self._build_toolbar()

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True,
                  padx=SP_XL, pady=(0, SP_SM))

        self._build_sidebar(main)

        right = ctk.CTkFrame(main, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)

        self._build_tree(right)
        self._build_preview(right)
        self._build_console_panel()
        self._build_status()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent", height=64)
        header.pack(fill="x", padx=SP_XL, pady=(SP_MD, SP_MD))
        header.pack_propagate(False)

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left")

        ctk.CTkLabel(left, text=">_",
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=dark(C.ACCENT)).pack(side="left")
        ctk.CTkLabel(left, text=f"  {APP_NAME}",
                     font=ctk.CTkFont(
                         family=C.ensure_font_family(),
                         size=22, weight="bold"),
                     text_color=dark(C.FG_BRIGHT)).pack(side="left")
        ctk.CTkLabel(left, text=f"  v{APP_VERSION}",
                     font=ctk.CTkFont(size=11),
                     text_color=dark(C.FG_DIM)).pack(
            side="left", padx=(0, SP_LG))

        self.clock = ctk.CTkLabel(left, text="",
                                   font=ctk.CTkFont(size=12),
                                   text_color=dark(C.ACCENT_2))
        self.clock.pack(side="left")
        self._tick_clock()

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right")

        for icon, cmd, color in [
            ("?", self._open_help, C.FG_MUTED),
            ("⚙", self._open_settings, C.FG),
            ("📊", self._open_stats, C.ACCENT),
            ("🕘", self._open_history, C.FG),
            ("▶", self._open_runlog, C.BASH),
            ("⏻", self.toggle_console, C.SUCCESS),
        ]:
            IconButton(right, icon, color=color,
                       command=cmd).pack(side="left", padx=SP_XS)

        ctk.CTkFrame(self, fg_color=dark(C.ACCENT),
                     height=1).pack(fill="x")

    def _build_toolbar(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=SP_XL, pady=SP_MD)

        self._search_bar = SearchBar(
            toolbar, textvariable=self.search_var,
            placeholder="Поиск по имени, категории, команде...")
        self._search_bar.pack(side="left", fill="x", expand=True,
                              padx=(0, SP_LG))
        self.search_var.trace_add("write", lambda *_: self.refresh())

        # ═══ 4 ФИЛЬТРА: Все / sh / bash / cmd ═══
        self._shell_seg = ctk.CTkSegmentedButton(
            toolbar,
            values=["Все", "📜 sh", "🐧 bash", "🪟 cmd"],
            height=H_BUTTON, corner_radius=R_SM,
            fg_color=dark(C.SURFACE_2),
            selected_color=dark(C.ACCENT),
            selected_hover_color=dark(C.ACCENT_2),
            unselected_color=dark(C.SURFACE_2),
            unselected_hover_color=dark(C.HOVER),
            text_color=dark(C.FG),
            font=ctk.CTkFont(size=12),
            command=self._on_shell_change)
        self._shell_seg.pack(side="left", padx=(0, SP_MD))
        self._shell_seg.set("Все")
        self.after(50, self._fix_seg_colors)

        self._fav_button = PillButton(
            toolbar, "☆ Избранное",
            color=C.FAVORITE,
            command=self._toggle_fav_filter)
        self._fav_button.pack(side="left", padx=(0, SP_MD))

        ctk.CTkButton(
            toolbar, text="+ Новая",
            height=H_BUTTON, corner_radius=R_SM,
            fg_color=dark(C.ACCENT),
            hover_color=dark(C.ACCENT_2),
            text_color=dark(C.BG),
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._add_command).pack(side="left")

    def _build_sidebar(self, parent):
        sidebar = ctk.CTkFrame(
            parent, fg_color=dark(C.SURFACE),
            corner_radius=R_LG, border_width=1,
            border_color=dark(C.BORDER_SOFT), width=240)
        sidebar.pack(side="left", fill="y", padx=(0, SP_LG))
        sidebar.pack_propagate(False)

        head = ctk.CTkFrame(sidebar, fg_color="transparent")
        head.pack(fill="x", padx=SP_MD, pady=(SP_MD, SP_SM))
        ctk.CTkFrame(head, fg_color=dark(C.ACCENT),
                     width=3, height=20).pack(side="left",
                                                padx=(0, SP_SM))
        ctk.CTkLabel(head, text="КАТЕГОРИИ",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=dark(C.FG_MUTED),
                     anchor="w").pack(side="left")

        self._cat_scroll = ctk.CTkScrollableFrame(
            sidebar, fg_color="transparent",
            scrollbar_button_color=dark(C.SURFACE_3),
            scrollbar_button_hover_color=dark(C.ACCENT))
        self._cat_scroll.pack(fill="both", expand=True,
                              padx=SP_XS, pady=(0, SP_SM))

    def _build_tree(self, parent):
        head = ctk.CTkFrame(parent, fg_color="transparent")
        head.pack(fill="x", pady=(0, SP_SM))
        ctk.CTkFrame(head, fg_color=dark(C.ACCENT),
                     width=3, height=20).pack(side="left",
                                                padx=(0, SP_SM))
        ctk.CTkLabel(head, text="КОМАНДЫ",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=dark(C.FG_MUTED),
                     anchor="w").pack(side="left")
        self._list_count = ctk.CTkLabel(
            head, text="", font=ctk.CTkFont(size=11),
            text_color=dark(C.FG_DIM), anchor="e")
        self._list_count.pack(side="right")

        wrap = ctk.CTkFrame(
            parent, fg_color=dark(C.SURFACE),
            corner_radius=R_LG, border_width=1,
            border_color=dark(C.BORDER_SOFT))
        wrap.pack(fill="both", expand=True)

        cols = ("pin", "name", "shell", "category", "uses", "favorite")
        self._tree = ttk.Treeview(
            wrap, columns=cols, show="headings",
            selectmode="extended", style="Keeper.Treeview")

        self._tree.heading("pin", text="📌")
        self._tree.heading("name", text="НАЗВАНИЕ")
        self._tree.heading("shell", text="SHELL")
        self._tree.heading("category", text="КАТЕГОРИЯ")
        self._tree.heading("uses", text="🔥")
        self._tree.heading("favorite", text="★")

        self._tree.column("pin", width=44, anchor="center",
                          stretch=False)
        self._tree.column("name", width=420, anchor="w")
        self._tree.column("shell", width=120, anchor="center",
                          stretch=False)
        self._tree.column("category", width=240, anchor="w")
        self._tree.column("uses", width=64, anchor="center",
                          stretch=False)
        self._tree.column("favorite", width=54, anchor="center",
                          stretch=False)
        self._tree.pack(side="left", fill="both", expand=True,
                        padx=1, pady=1)

        sb = ttk.Scrollbar(wrap, orient="vertical",
                           command=self._tree.yview,
                           style="Keeper.Vertical.TScrollbar")
        sb.pack(side="right", fill="y")
        self._tree.configure(yscrollcommand=sb.set)

        self._tree.tag_configure("fav", foreground=dark(C.FAVORITE))
        self._tree.tag_configure("pinned", foreground=dark(C.PINNED))
        self._tree.tag_configure("odd", background=dark(C.SURFACE_2))
        self._tree.tag_configure("even", background=dark(C.SURFACE))
        # Приглушённый цвет для недоступных команд
        self._tree.tag_configure("unavailable",
                                  foreground=dark(C.FG_DIM))

        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.bind("<Double-1>", self._on_double_click)
        self._tree.bind("<ButtonRelease-3>", self._show_context_menu)

    def _build_preview(self, parent):
        ctk.CTkFrame(parent, fg_color=dark(C.BORDER_SOFT),
                     height=1).pack(fill="x", pady=(SP_MD, 0))

        preview = ctk.CTkFrame(parent, fg_color="transparent")
        preview.pack(fill="x", pady=(SP_SM, 0))

        head = ctk.CTkFrame(preview, fg_color="transparent")
        head.pack(fill="x", pady=(0, SP_SM))
        ctk.CTkFrame(head, fg_color=dark(C.ACCENT),
                     width=3, height=20).pack(side="left",
                                                padx=(0, SP_SM))
        ctk.CTkLabel(head, text="ПРЕДПРОСМОТР",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=dark(C.FG_MUTED)).pack(side="left")

        self._shell_badge = ctk.CTkLabel(
            head, text="", fg_color=dark(C.SURFACE_2),
            text_color=dark(C.FG_MUTED), corner_radius=R_SM,
            font=ctk.CTkFont(size=10, weight="bold"),
            padx=SP_SM, pady=2)
        self._shell_badge.pack(side="left", padx=(SP_MD, 0))

        self._detail_name = ctk.CTkLabel(
            head, text="— не выбрано —",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=dark(C.FG_MUTED), anchor="w")
        self._detail_name.pack(side="left", padx=(SP_LG, 0))

        self._detail_meta = ctk.CTkLabel(
            head, text="", font=ctk.CTkFont(size=10),
            text_color=dark(C.FG), anchor="e")
        self._detail_meta.pack(side="right")

        text_wrap = ctk.CTkFrame(
            preview, fg_color=dark(C.SURFACE_2),
            corner_radius=R_MD, border_width=1,
            border_color=dark(C.BORDER_SOFT))
        text_wrap.pack(fill="x", pady=(0, SP_SM))

        self._detail_text = ctk.CTkTextbox(
            text_wrap, fg_color="transparent", border_width=0,
            text_color=dark(C.ACCENT_2),
            font=ctk.CTkFont(
                family=C.ensure_font_family(), size=11),
            height=80)
        self._detail_text.pack(fill="x", padx=SP_MD, pady=SP_SM)
        self._detail_text.configure(state="disabled")

        # Действия — кнопка "Запустить" УБРАНА
        actions = ctk.CTkFrame(preview, fg_color="transparent")
        actions.pack(fill="x")

        ctk.CTkButton(
            actions, text="📋  Копировать",
            height=H_BUTTON, corner_radius=R_SM,
            fg_color=dark(C.ACCENT),
            hover_color=dark(C.ACCENT_2),
            text_color=dark(C.BG),
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._copy_selected).pack(side="left",
                                                padx=(0, SP_SM))

        ctk.CTkButton(
            actions, text="✏  Изменить",
            height=H_BUTTON, corner_radius=R_SM,
            fg_color="transparent",
            hover_color=dark(C.HOVER),
            text_color=dark(C.FG),
            border_width=1,
            border_color=dark(C.BORDER_SOFT),
            font=ctk.CTkFont(size=12),
            command=self._edit_selected).pack(side="left",
                                                padx=(0, SP_SM))

        ctk.CTkButton(
            actions, text="🗑  Удалить",
            height=H_BUTTON, corner_radius=R_SM,
            fg_color="transparent",
            hover_color=dark(C.DANGER),
            text_color=dark(C.DANGER),
            border_width=1,
            border_color=dark(C.DANGER),
            font=ctk.CTkFont(size=12),
            command=self._delete_selected).pack(side="right")

    # ─── CONSOLE PANEL ───
    def _build_console_panel(self):
        self.console_frame = ctk.CTkFrame(self, fg_color="transparent")

        head = ctk.CTkFrame(self.console_frame, fg_color="transparent")
        head.pack(fill="x", padx=SP_XL, pady=(SP_SM, 0))

        ctk.CTkFrame(head, fg_color=dark(C.ACCENT),
                     width=3, height=18).pack(side="left",
                                                padx=(0, SP_SM))
        ctk.CTkLabel(head, text="ВСТРОЕННЫЙ ТЕРМИНАЛ",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=dark(C.FG_MUTED),
                     anchor="w").pack(side="left")

        self._mode_badge = ctk.CTkLabel(
            head, text="● EMBEDDED",
            fg_color=dark(C.ACCENT),
            text_color=dark(C.BG),
            corner_radius=R_SM,
            font=ctk.CTkFont(size=10, weight="bold"),
            padx=SP_SM, pady=2)
        self._mode_badge.pack(side="left", padx=(SP_SM, 0))

        ctk.CTkButton(
            head, text="▾  Скрыть",
            width=90, height=26, corner_radius=R_SM,
            fg_color="transparent",
            hover_color=dark(C.HOVER),
            text_color=dark(C.FG_MUTED),
            border_width=1,
            border_color=dark(C.BORDER_SOFT),
            font=ctk.CTkFont(size=11),
            command=self.toggle_console).pack(side="right")

        wrap = ctk.CTkFrame(
            self.console_frame, fg_color=dark(C.SURFACE),
            corner_radius=R_MD, border_width=1,
            border_color=dark(C.BORDER_SOFT))
        wrap.pack(fill="both", expand=True,
                  padx=SP_XL, pady=(SP_SM, SP_SM))

        try:
            self.console = EmbeddedConsole(
                wrap, self.ctx,
                shell=self.ctx.get("term_shell", "auto"),
                font_size=self.ctx.get("term_font_size", 10))
            self.console.pack(fill="both", expand=True,
                              padx=1, pady=1)
        except Exception as e:
            log.error("EmbeddedConsole create failed: %s", e)
            self.console = None

        self._console_visible = False

    def toggle_console(self):
        if not hasattr(self, "console_frame"):
            self._build_console_panel()

        self._console_visible = not self._console_visible
        if self._console_visible:
            try:
                self.console_frame.pack(fill="both", expand=False,
                                         side="bottom")
            except Exception as e:
                log.warning("console pack: %s", e)
            if self.console:
                self.after(80, self.console._focus_input)
        else:
            try:
                self.console_frame.pack_forget()
            except Exception:
                pass

    # ─── STATUS BAR ───
    def _build_status(self):
        ctk.CTkFrame(self, fg_color=dark(C.BORDER_SOFT),
                     height=1).pack(fill="x")

        status = ctk.CTkFrame(self, fg_color="transparent",
                              height=H_STATUS)
        status.pack(fill="x", side="bottom",
                    padx=SP_XL, pady=SP_SM)
        status.pack_propagate(False)

        left = ctk.CTkFrame(status, fg_color="transparent")
        left.pack(side="left")

        ctk.CTkButton(left, text="+ Новая",
                      height=H_BUTTON, corner_radius=R_SM,
                      fg_color=dark(C.ACCENT),
                      hover_color=dark(C.ACCENT_2),
                      text_color=dark(C.BG),
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=self._add_command).pack(
            side="left", padx=(0, SP_SM))

        ctk.CTkButton(left, text="⬆ Экспорт",
                      height=H_BUTTON, corner_radius=R_SM,
                      fg_color="transparent",
                      hover_color=dark(C.HOVER),
                      text_color=dark(C.FG_MUTED),
                      border_width=1,
                      border_color=dark(C.BORDER_SOFT),
                      font=ctk.CTkFont(size=12),
                      command=self._export_data).pack(
            side="left", padx=(0, SP_SM))

        ctk.CTkButton(left, text="⬇ Импорт",
                      height=H_BUTTON, corner_radius=R_SM,
                      fg_color="transparent",
                      hover_color=dark(C.HOVER),
                      text_color=dark(C.FG_MUTED),
                      border_width=1,
                      border_color=dark(C.BORDER_SOFT),
                      font=ctk.CTkFont(size=12),
                      command=self._import_data).pack(side="left")

        center = ctk.CTkFrame(status, fg_color="transparent")
        center.pack(side="left", padx=SP_XL)

        self._badge_count = Badge(center, "0/0",
                                   color=C.ACCENT, icon="≡")
        self._badge_count.pack(side="left", padx=SP_XS)
        self._badge_fav = Badge(center, "0",
                                 color=C.FAVORITE, icon="★")
        self._badge_fav.pack(side="left", padx=SP_XS)
        self._badge_uses = Badge(center, "0",
                                  color=C.WARNING, icon="🔥")
        self._badge_uses.pack(side="left", padx=SP_XS)

        right = ctk.CTkFrame(status, fg_color="transparent")
        right.pack(side="right")
        self._status_label = ctk.CTkLabel(
            right, text="", font=ctk.CTkFont(size=10),
            text_color=dark(C.FG_MUTED))
        self._status_label.pack(side="right")

    # ─── HOTKEYS ───
    def _bind_hotkeys(self):
        self.bind("<Control-n>", lambda e: self._add_command())
        self.bind("<Control-f>", lambda e: self._focus_search())
        self.bind("<Control-c>", lambda e: self._copy_selected())
        self.bind("<Control-e>", lambda e: self._edit_selected())
        self.bind("<Control-d>", lambda e: self._duplicate_selected())
        self.bind("<Delete>", lambda e: self._delete_selected())
        self.bind("<Control-h>", lambda e: self._open_runlog())
        self.bind("<Control-comma>", lambda e: self._open_settings())
        self.bind("<Control-s>", lambda e: self._open_stats())
        self.bind("<Escape>", lambda e: self._clear_filters())
        self.bind("<F5>", lambda e: self._hard_refresh())
        self.bind("<F1>", lambda e: self._open_help())
        self.bind("<Control-grave>", lambda e: self.toggle_console())

    def _focus_search(self):
        try:
            self._search_bar.focus()
        except Exception as e:
            log.warning("focus_search: %s", e)

    def _clear_filters(self):
        try:
            self.search_var.set("")
            self.category_filter.set("")
            self.shell_filter.set("all")
            self.only_fav = False
            if self._shell_seg:
                self._shell_seg.set("Все")
            if self._fav_button:
                self._fav_button.set_active(False)
                self._fav_button.configure(text="☆ Избранное")
            self.refresh()
            self._update_categories()
        except Exception as e:
            log.warning("clear_filters: %s", e)

    def _hard_refresh(self):
        try:
            self.storage = Storage(DATA_FILE, self.ctx)
            self.refresh()
            self._update_categories()
            Toast.show(self, "Данные перезагружены",
                       C.SUCCESS, icon="✓")
        except Exception as e:
            Toast.show(self, f"Ошибка: {e}", C.DANGER, icon="⚠")

    def _tick_clock(self):
        try:
            self.clock.configure(
                text=datetime.now().strftime("%H:%M:%S"))
        except Exception:
            pass
        self.after(1000, self._tick_clock)

    # ─── FILTERS ───
    def _on_shell_change(self, value):
        mapping = {
            "Все": "all",
            "📜 sh": "sh",
            "🐧 bash": "bash",
            "🪟 cmd": "cmd",
        }
        self.shell_filter.set(mapping.get(value, "all"))
        self.refresh()
        self.after(30, self._fix_seg_colors)

    def _fix_seg_colors(self):
        try:
            seg = self._shell_seg
            active_val = seg.get()
            buttons = getattr(seg, "_buttons_dict", {})
            for val, btn in buttons.items():
                is_active = (val == active_val)
                color = dark(C.BG) if is_active else dark(C.FG)
                weight = "bold" if is_active else "normal"
                if hasattr(btn, "_text_label") and btn._text_label:
                    try:
                        btn._text_label.configure(
                            fg=color,
                            font=(C.ensure_font_family(),
                                  12, weight))
                    except Exception:
                        pass
                try:
                    btn.configure(
                        text_color=color,
                        font=ctk.CTkFont(size=12, weight=weight))
                except Exception:
                    pass
        except Exception as e:
            log.warning("_fix_seg_colors: %s", e)

    def _toggle_fav_filter(self):
        self.only_fav = not self.only_fav
        if self.only_fav:
            self._fav_button.set_active(True)
            self._fav_button.configure(text="★ Избранное")
        else:
            self._fav_button.set_active(False)
            self._fav_button.configure(text="☆ Избранное")
        self.refresh()

    # ─── CATEGORIES ───
    def _update_categories(self):
        if not getattr(self, "_cat_scroll", None):
            return
        for w in self._cat_scroll.winfo_children():
            w.destroy()
        self._cat_buttons = {}
        self._make_cat_btn("", "▸  Все", len(self.storage.all()))
        cats = self.storage.categories()
        if cats:
            sep = ctk.CTkFrame(self._cat_scroll,
                                fg_color=dark(C.BORDER_SOFT),
                                height=1)
            sep.pack(fill="x", pady=SP_SM, padx=SP_SM)
        for cat, count in cats:
            self._make_cat_btn(cat, f"#  {cat}", count)
        self._paint_categories()

    def _make_cat_btn(self, value, label, count):
        row = ctk.CTkFrame(
            self._cat_scroll, fg_color="transparent",
            corner_radius=R_SM, height=32, cursor="hand2")
        row.pack(fill="x", padx=SP_XS, pady=1)
        row.pack_propagate(False)

        lbl = ctk.CTkLabel(row, text=label,
                           font=ctk.CTkFont(size=12),
                           text_color=dark(C.FG), anchor="w")
        lbl.pack(side="left", padx=(SP_SM, 0))

        cnt = ctk.CTkLabel(row, text=str(count),
                           font=ctk.CTkFont(size=10),
                           text_color=dark(C.FG_DIM))
        cnt.pack(side="right", padx=(0, SP_SM))

        def on_click(_e=None):
            if self.category_filter.get() == value:
                self.category_filter.set("")
            else:
                self.category_filter.set(value)
            self.refresh()
            self._paint_categories()

        def on_enter(_e=None):
            if self.category_filter.get() != value:
                for w in (row, lbl, cnt):
                    w.configure(fg_color=dark(C.HOVER))

        def on_leave(_e=None):
            if self.category_filter.get() != value:
                for w in (row, lbl, cnt):
                    w.configure(fg_color="transparent")

        for w in (row, lbl, cnt):
            w.bind("<Button-1>", on_click)
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

        self._cat_buttons[value] = (row, lbl, cnt)

    def _paint_categories(self):
        active = self.category_filter.get()
        for value, (row, lbl, cnt) in self._cat_buttons.items():
            if value == active:
                row.configure(fg_color=dark(C.ACCENT))
                lbl.configure(text_color=dark(C.BG),
                              font=ctk.CTkFont(size=12, weight="bold"))
                cnt.configure(text_color=dark(C.BG))
            else:
                row.configure(fg_color="transparent")
                lbl.configure(text_color=dark(C.FG),
                              font=ctk.CTkFont(size=12))
                cnt.configure(text_color=dark(C.FG_DIM))

    # ─── REFRESH ───
    def refresh(self):
        if not hasattr(self, "_tree"):
            return
        try:
            query = self.search_var.get().lower().strip()
            sf = self.shell_filter.get()
            only_fav = self.only_fav
            cat_filter = self.category_filter.get()

            self._filtered = []
            for idx, cmd in enumerate(self.storage.all()):
                if sf != "all" and cmd.get("shell") != sf:
                    continue
                if only_fav and not cmd.get("favorite"):
                    continue
                if cat_filter:
                    tags = [t.strip()
                            for t in re.split(
                                r"[,\s]+",
                                cmd.get("category", ""))
                            if t.strip()]
                    if cat_filter not in tags:
                        continue
                if query:
                    hay = (f"{cmd.get('name','')} "
                           f"{cmd.get('category','')} "
                           f"{cmd.get('text','')}")
                    if query.lower() not in hay.lower():
                        continue
                self._filtered.append((idx, cmd))

            sort_mode = self.ctx.get("sort_mode", "smart")
            if sort_mode == "smart":
                self._filtered.sort(key=lambda x: (
                    not x[1].get("pinned", False),
                    not x[1].get("favorite", False),
                    -x[1].get("uses", 0),
                    x[1].get("name", "").lower()))
            elif sort_mode == "name":
                self._filtered.sort(
                    key=lambda x: x[1].get("name", "").lower())
            elif sort_mode == "uses":
                self._filtered.sort(
                    key=lambda x: -x[1].get("uses", 0))
            elif sort_mode == "favorite":
                self._filtered.sort(key=lambda x: (
                    not x[1].get("favorite", False),
                    x[1].get("name", "").lower()))
            else:
                self._filtered.sort(
                    key=lambda x: x[1].get("name", "").lower())

            for item in self._tree.get_children():
                self._tree.delete(item)

            for i, (orig_idx, cmd) in enumerate(self._filtered):
                shell = cmd.get("shell", "")
                tags = [str(orig_idx),
                        "even" if i % 2 == 0 else "odd"]
                if cmd.get("favorite"):
                    tags.append("fav")
                if cmd.get("pinned"):
                    tags.append("pinned")
                # Приглушённый цвет для недоступных shell
                if not is_shell_available(shell):
                    tags.append("unavailable")

                icon = get_shell_icon(shell)
                self._tree.insert(
                    "", "end", iid=str(i),
                    values=(
                        "📌" if cmd.get("pinned") else "",
                        cmd.get("name", ""),
                        f"{icon} {shell.upper()}",
                        cmd.get("category", ""),
                        cmd.get("uses", 0) or "",
                        "★" if cmd.get("favorite") else "",
                    ),
                    tags=tuple(tags))

            total = len(self.storage.all())
            shown = len(self._filtered)
            favs = sum(1 for c in self.storage.all()
                       if c.get("favorite"))
            total_uses = sum(c.get("uses", 0)
                             for c in self.storage.all())

            if self._list_count:
                self._list_count.configure(
                    text=f"показано {shown} из {total}")
            if self._badge_count:
                self._badge_count.set_text(f"{shown}/{total}")
                self._badge_fav.set_text(str(favs))
                self._badge_uses.set_text(str(total_uses))
            if self._status_label:
                self._status_label.configure(
                    text=f"Тема: {C.name}  ·  "
                         f"Storage: {total} команд")

        except Exception as e:
            log.exception("refresh: %s", e)

    def _get_selected_cmd(self):
        sel = self._tree.selection()
        if not sel:
            return None
        try:
            i = int(sel[0])
            if 0 <= i < len(self._filtered):
                return self._filtered[i]
        except Exception:
            pass
        return None

    def _on_select(self, _event=None):
        cur = self._get_selected_cmd()
        if not cur:
            self._detail_name.configure(
                text="— не выбрано —",
                text_color=dark(C.FG_MUTED))
            self._detail_meta.configure(text="")
            self._shell_badge.configure(
                text="", fg_color=dark(C.SURFACE_2))
            self._detail_text.configure(state="normal")
            self._detail_text.delete("1.0", "end")
            self._detail_text.insert(
                "1.0",
                "↑  Выбери команду из списка,\n"
                "    чтобы увидеть её текст здесь.\n\n"
                "    Двойной клик — копировать.\n"
                "    Ctrl+E — изменить.")
            self._detail_text.configure(state="disabled")
            return

        idx, cmd = cur
        shell = cmd.get("shell", "")
        color_key = get_shell_color_key(shell)
        color = getattr(C, color_key, C.FG)
        icon = get_shell_icon(shell)

        self._detail_name.configure(text=cmd.get("name", ""),
                                     text_color=dark(C.ACCENT_2))
        self._shell_badge.configure(
            text=f" {icon} {shell.upper()} ",
            fg_color=dark(color), text_color=dark(C.BG))

        meta = []
        if cmd.get("category"):
            meta.append(f"#{cmd['category']}")
        if cmd.get("uses"):
            meta.append(f"🔥 {cmd['uses']}")
        if cmd.get("favorite"):
            meta.append("★")
        if cmd.get("pinned"):
            meta.append("📌")
        if not is_shell_available(shell):
            meta.append("⚠ не запустится")
        self._detail_meta.configure(text="   ".join(meta))

        self._detail_text.configure(state="normal")
        self._detail_text.delete("1.0", "end")
        self._detail_text.insert("1.0", cmd.get("text", ""))
        self._detail_text.configure(state="disabled")

    def _on_double_click(self, event):
        region = self._tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        self._copy_selected()

    # ─── ACTIONS ───
    def _copy_selected(self):
        cur = self._get_selected_cmd()
        if not cur:
            Toast.show(self, "Выбери команду", C.DANGER, icon="⚠")
            return
        idx, cmd = cur
        self.clipboard_clear()
        self.clipboard_append(cmd.get("text", ""))
        self.update()
        self.storage.all()[idx]["uses"] = cmd.get("uses", 0) + 1
        self.storage.mark_dirty()
        self.refresh()
        Toast.show(self, f"Скопировано: {cmd.get('name')}",
                   C.ACCENT, icon="📋")

    def _add_command(self):
        cats = [c for c, _ in self.storage.categories()]
        dlg = CommandDialog(self, self.ctx, "Новая команда",
                            all_categories=cats)
        self.wait_window(dlg)
        if dlg.result:
            self.storage.add(dlg.result)
            self.storage.add_history("add",
                                      dlg.result.get("name", ""))
            self.storage.save()
            self.refresh()
            self._update_categories()
            Toast.show(self, f"Добавлено: {dlg.result['name']}",
                       C.SUCCESS, icon="✓")

    def _edit_selected(self):
        cur = self._get_selected_cmd()
        if not cur:
            Toast.show(self, "Выбери команду", C.DANGER, icon="⚠")
            return
        idx, cmd = cur
        cats = [c for c, _ in self.storage.categories()]
        dlg = CommandDialog(self, self.ctx, "Редактирование",
                            cmd, all_categories=cats)
        self.wait_window(dlg)
        if dlg.result:
            self.storage.update(idx, dlg.result)
            self.storage.add_history("edit",
                                      dlg.result.get("name", ""))
            self.storage.save()
            self.refresh()
            self._update_categories()
            Toast.show(self, f"Сохранено: {dlg.result['name']}",
                       C.SUCCESS, icon="✓")

    def _duplicate_selected(self):
        cur = self._get_selected_cmd()
        if not cur:
            Toast.show(self, "Выбери команду", C.DANGER, icon="⚠")
            return
        idx, cmd = cur
        new_idx = self.storage.duplicate(idx)
        if new_idx is not None:
            self.storage.save()
            self.refresh()
            self._update_categories()
            Toast.show(self, f"Дубликат: {cmd.get('name')}",
                       C.ACCENT_2, icon="📄")

    def _delete_selected(self):
        cur = self._get_selected_cmd()
        if not cur:
            Toast.show(self, "Выбери команду", C.DANGER, icon="⚠")
            return
        idx, cmd = cur
        if self.ctx.get("confirm_delete", True):
            if not messagebox.askyesno(
                    "Удаление",
                    f"Удалить «{cmd.get('name')}»?",
                    parent=self):
                return
        self.storage.delete(idx)
        self.storage.add_history("delete", cmd.get("name", ""))
        self.storage.save()
        self.refresh()
        self._update_categories()
        Toast.show(self, "Удалено", C.DANGER, icon="🗑")

    def _toggle_fav_selected(self):
        cur = self._get_selected_cmd()
        if not cur:
            return
        idx, cmd = cur
        cmd["favorite"] = not cmd.get("favorite", False)
        self.storage.update(idx, cmd)
        self.refresh()
        Toast.show(self, "Избранное переключено",
                   C.FAVORITE, icon="★")

    def _toggle_pin_selected(self):
        cur = self._get_selected_cmd()
        if not cur:
            return
        idx, cmd = cur
        cmd["pinned"] = not cmd.get("pinned", False)
        self.storage.update(idx, cmd)
        self.refresh()
        Toast.show(self, "Пин переключён", C.PINNED, icon="📌")

    def _show_context_menu(self, event):
        row = self._tree.identify_row(event.y)
        if not row:
            return
        if row not in self._tree.selection():
            self._tree.selection_set(row)

        items = [
            ("📋", "Копировать", "Ctrl+C", self._copy_selected),
            "---",
            ("✏", "Изменить", "Ctrl+E", self._edit_selected),
            ("📄", "Дублировать", "Ctrl+D", self._duplicate_selected),
            "---",
            ("★", "Избранное", "", self._toggle_fav_selected),
            ("📌", "Пин / Снять", "", self._toggle_pin_selected),
            "---",
            ("🗑", "Удалить", "Del", self._delete_selected),
        ]
        ContextMenu(self, items, event.x_root, event.y_root)

    # ─── EXPORT / IMPORT ───
    def _export_data(self):
        path = filedialog.asksaveasfilename(
            parent=self, defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile=(f"compmentem_"
                         f"{datetime.now().strftime('%Y%m%d')}.json"))
        if not path:
            return
        try:
            self.storage.export(path)
            self.storage.add_history("export", Path(path).name)
            self.storage.save()
            Toast.show(self, f"Экспорт: {Path(path).name}",
                       C.SUCCESS, icon="⬆")
        except Exception as e:
            Toast.show(self, f"{e}", C.DANGER, icon="⚠")

    def _import_data(self):
        path = filedialog.askopenfilename(
            parent=self,
            filetypes=[("JSON", "*.json"), ("Все файлы", "*.*")])
        if not path:
            return

        dlg = ctk.CTkToplevel(self)
        dlg.title("Импорт команд")
        dlg.geometry("460x300")
        dlg.configure(fg_color=dark(C.BG))
        dlg.transient(self)
        dlg.grab_set()

        ctk.CTkLabel(dlg, text="Как обработать совпадения?",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=dark(C.FG_BRIGHT)).pack(pady=SP_LG)

        var = tk.StringVar(value="merge")
        for value, label in [
            ("merge", "Объединить (взять максимум)"),
            ("replace", "Перезаписать"),
            ("skip", "Пропустить"),
        ]:
            ctk.CTkRadioButton(
                dlg, text=label,
                variable=var, value=value,
                fg_color=dark(C.ACCENT),
                hover_color=dark(C.ACCENT_2),
                text_color=dark(C.FG),
                font=ctk.CTkFont(size=12)).pack(anchor="w",
                                                  padx=SP_XL)

        result = {"ok": False}

        def do_import():
            result["ok"] = True
            dlg.destroy()

        row = ctk.CTkFrame(dlg, fg_color="transparent")
        row.pack(pady=SP_LG)
        ctk.CTkButton(
            row, text="Отмена",
            fg_color="transparent",
            hover_color=dark(C.HOVER),
            text_color=dark(C.FG),
            border_width=1,
            border_color=dark(C.BORDER_SOFT),
            height=H_BUTTON, corner_radius=R_SM,
            command=dlg.destroy).pack(side="right",
                                        padx=(SP_SM, 0))
        ctk.CTkButton(
            row, text="✓  Импорт",
            fg_color=dark(C.ACCENT),
            hover_color=dark(C.ACCENT_2),
            text_color=dark(C.BG),
            font=ctk.CTkFont(weight="bold"),
            height=H_BUTTON, corner_radius=R_SM,
            command=do_import).pack(side="right")

        self.wait_window(dlg)
        if not result["ok"]:
            return

        try:
            added, replaced, skipped = self.storage.import_(
                path, var.get())
            self.storage.add_history(
                "import",
                f"{added}+{replaced} из {Path(path).name}")
            self.storage.save()
            self.refresh()
            self._update_categories()
            Toast.show(self,
                       f"Импорт: +{added} ~{replaced} -{skipped}",
                       C.SUCCESS, icon="⬇")
        except Exception as e:
            Toast.show(self, f"{e}", C.DANGER, icon="⚠")

    # ─── DIALOGS ───
    def _open_settings(self):
        def apply():
            try:
                for w in self.winfo_children():
                    w.destroy()
                self.configure(fg_color=dark(C.BG))
                self._setup_treeview_style()
                self._build_ui()
                self.refresh()
                self._update_categories()
                Toast.show(self, "Настройки применены",
                           C.SUCCESS, icon="⚙")
            except Exception as e:
                log.exception("apply settings: %s", e)

        SettingsDialog(self, self.ctx, on_apply=apply)

    def _open_stats(self):
        StatsDialog(self, self.storage)

    def _open_history(self):
        HistoryDialog(self, self.storage.history)

    def _open_runlog(self):
        RunLogDialog(self, self.storage.runlog)

    def _open_help(self):
        help_win = ctk.CTkToplevel(self)
        help_win.title("Справка")
        help_win.geometry("640x740")
        help_win.configure(fg_color=dark(C.BG))
        help_win.transient(self)
        help_win.grab_set()

        self.update_idletasks()
        px = self.winfo_rootx() + (self.winfo_width() - 640) // 2
        py = self.winfo_rooty() + (self.winfo_height() - 740) // 2
        help_win.geometry(f"640x740+{max(0, px)}+{max(0, py)}")

        header = ctk.CTkFrame(help_win, fg_color="transparent",
                              height=64)
        header.pack(fill="x", padx=SP_XL, pady=(SP_LG, SP_SM))
        header.pack_propagate(False)
        ctk.CTkFrame(header, fg_color=dark(C.ACCENT),
                     width=3, height=28).pack(side="left",
                                                padx=(0, SP_MD))
        ctk.CTkLabel(header, text="?  СПРАВКА",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=dark(C.FG_BRIGHT)).pack(
            side="left", fill="x", expand=True)
        ctk.CTkFrame(help_win, fg_color=dark(C.BORDER_SOFT),
                     height=1).pack(fill="x", padx=SP_XL)

        scroll = ctk.CTkScrollableFrame(
            help_win, fg_color="transparent",
            scrollbar_button_color=dark(C.SURFACE_3),
            scrollbar_button_hover_color=dark(C.ACCENT))
        scroll.pack(fill="both", expand=True,
                    padx=SP_XL, pady=SP_LG)

        sections = [
            ("УПРАВЛЕНИЕ", [
                ("Ctrl+N", "Новая команда"),
                ("Ctrl+E", "Редактировать"),
                ("Ctrl+D", "Дублировать"),
                ("Delete", "Удалить"),
            ]),
            ("РАБОТА С КОМАНДАМИ", [
                ("Ctrl+C", "Копировать"),
                ("Ctrl+`", "Встроенный терминал"),
                ("Двойной клик", "Копировать"),
                ("ПКМ", "Контекстное меню"),
            ]),
            ("НАВИГАЦИЯ", [
                ("Ctrl+F", "Фокус в поиск"),
                ("Esc", "Сбросить фильтры"),
                ("F5", "Перезагрузить"),
            ]),
            ("ОКНА", [
                ("Ctrl+H", "Журнал запусков"),
                ("Ctrl+S", "Статистика"),
                ("Ctrl+,", "Настройки"),
                ("F1", "Эта справка"),
            ]),
            ("ФИЛЬТРЫ", [
                ("Все / sh / bash / cmd", "Табы в тулбаре"),
                ("☆ Избранное", "Только избранные"),
                ("# категория", "Фильтр по категории"),
                ("Поиск", "Имя / категория / команда"),
            ]),
            ("SHELL", [
                ("📜 sh", "POSIX-стандарт (Linux, macOS, BSD)"),
                ("🐧 bash", "Linux/macOS shell"),
                ("🪟 cmd", "Windows (только категоризация на Linux)"),
            ]),
        ]

        for title, items in sections:
            head_row = ctk.CTkFrame(scroll, fg_color="transparent")
            head_row.pack(fill="x", pady=(SP_LG, SP_SM))
            ctk.CTkFrame(head_row, fg_color=dark(C.ACCENT),
                         width=3, height=18).pack(side="left",
                                                    padx=(0, SP_SM))
            ctk.CTkLabel(head_row, text=title,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=dark(C.FG_MUTED),
                         anchor="w").pack(side="left",
                                            fill="x", expand=True)

            for keys, desc in items:
                row = ctk.CTkFrame(scroll, fg_color="transparent")
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=keys,
                             font=ctk.CTkFont(size=11, weight="bold"),
                             text_color=dark(C.ACCENT_2),
                             width=200,
                             anchor="w").pack(side="left",
                                                padx=(SP_MD, 0))
                ctk.CTkLabel(row, text=desc,
                             font=ctk.CTkFont(size=11),
                             text_color=dark(C.FG),
                             anchor="w").pack(side="left",
                                                fill="x",
                                                expand=True)

        ctk.CTkFrame(help_win, fg_color=dark(C.BORDER_SOFT),
                     height=1).pack(fill="x", padx=SP_XL)
        footer = ctk.CTkFrame(help_win, fg_color="transparent")
        footer.pack(fill="x", padx=SP_XL, pady=SP_LG)
        ctk.CTkLabel(footer, text=f"{APP_NAME} v{APP_VERSION}",
                     font=ctk.CTkFont(size=10),
                     text_color=dark(C.FG_DIM)).pack(side="left")
        ctk.CTkButton(footer, text="Закрыть",
                      width=140, height=H_BUTTON, corner_radius=R_SM,
                      fg_color=dark(C.ACCENT),
                      hover_color=dark(C.ACCENT_2),
                      text_color=dark(C.BG),
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=help_win.destroy).pack(side="right")
        help_win.bind("<Escape>", lambda e: help_win.destroy())

    # ─── CLEANUP ───
    def _on_close(self):
        try:
            if self.console:
                self.console.shutdown()
        except Exception:
            pass
        try:
            self.runner.cleanup()
        except Exception:
            pass
        try:
            self.storage.flush()
        except Exception:
            pass
        self.destroy()


# ═══════════════════════════════════════════════════════════════════════════
#  ТОЧКА ВХОДА
# ═══════════════════════════════════════════════════════════════════════════

def main():
    _setup_logging()
    log.info("Запуск %s v%s", APP_NAME, APP_VERSION)

    if not acquire_lock():
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning(
            APP_NAME,
            "Приложение уже запущено в другом окне.")
        root.destroy()
        sys.exit(0)

    app = MainWindow(CTX)
    app.mainloop()


if __name__ == "__main__":
    main()

# ═══ КОНЕЦ ФАЙЛА ═══
