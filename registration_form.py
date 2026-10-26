"""
Week 6 Practical - Input Validation
===================================

A Tkinter registration form that validates every field before accepting it:

* Full name is required (and cannot be only spaces).
* Age must be a whole number from 0 to 120.
* Email must match name@domain.tld.

Optional extensions included:
* Live email validation as the user types.
* Valid registrations are saved to a local SQLite database.

Run with:
    python registration_form.py
"""

from __future__ import annotations

import re
import sqlite3
import tkinter as tk
from contextlib import closing
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EMAIL_PATTERN = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"

PROJECT_DIR = Path(__file__).resolve().parent
DB_PATH = PROJECT_DIR / "registrations.db"

FONT = "Segoe UI"

ROOT_BG = "#F3F6F5"
CARD_BG = "#FFFFFF"
FIELD_BG = "#FBFCFB"
TEXT_COLOR = "#1F2933"
MUTED_COLOR = "#6B7280"
BORDER_COLOR = "#D7E1DC"
ERROR_COLOR = "#C0453A"
SUCCESS_COLOR = "#2E9E6D"
ACCENT_COLOR = "#2E9E6D"
ACCENT_HOVER = "#257D57"

FIELD_ORDER = ("name", "age", "email")
FIELD_LABELS = {"name": "Full name", "age": "Age", "email": "Email"}


# ---------------------------------------------------------------------------
# Validation - each function returns an error message or None
# ---------------------------------------------------------------------------

def validate_required(value: str, field_name: str) -> str | None:
    """Return an error when *value* is blank or contains only spaces."""
    if value.strip() == "":
        return f"{field_name} is required."
    return None


def validate_age(value: str) -> str | None:
    """Return an error unless *value* is a whole number from 0 to 120."""
    try:
        age = int(value.strip())
    except ValueError:
        return "Age must be a whole number."

    if age < 0 or age > 120:
        return "Age must be between 0 and 120."
    return None


def validate_email(value: str) -> str | None:
    """Return an error unless *value* looks like name@domain.tld."""
    value = value.strip()
    if value == "":
        return "Email is required."
    if re.match(EMAIL_PATTERN, value) is None:
        return "Enter a valid email address, e.g. name@example.com"
    return None


def validate_registration(
    name: str, age: str, email: str
) -> dict[str, str | None]:
    """Run every field check once and return the errors keyed by field."""
    return {
        "name": validate_required(name, "Full name"),
        "age": validate_age(age),
        "email": validate_email(email),
    }


# ---------------------------------------------------------------------------
# SQLite helpers (optional extension)
# ---------------------------------------------------------------------------

def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """Create the local registrations table if it does not exist yet."""
    with closing(_connect()) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS registrations (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL,
                age        INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
                email      TEXT    NOT NULL,
                created_at TEXT    NOT NULL
            )
            """
        )


def save_registration(name: str, age: int, email: str) -> int:
    """Insert one validated registration and return its row id."""
    with closing(_connect()) as conn, conn:
        cursor = conn.execute(
            """
            INSERT INTO registrations (name, age, email, created_at)
            VALUES (?, ?, ?, datetime('now', 'localtime'))
            """,
            (name, age, email),
        )
        return int(cursor.lastrowid)


def count_registrations() -> int:
    """Return how many rows are currently stored in the local database."""
    with closing(_connect()) as conn:
        row = conn.execute("SELECT COUNT(*) FROM registrations").fetchone()
    return int(row[0]) if row else 0


# ---------------------------------------------------------------------------
# Tkinter application
# ---------------------------------------------------------------------------

class RegistrationApp(tk.Tk):
    """Registration form window with inline, field-specific validation."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Registration Form")
        self.configure(bg=ROOT_BG)
        self.resizable(False, False)
        self.attempted_submit = False
        self.fields: dict[str, dict[str, object]] = {}

        self._place_window()
        self._build_ui()

        try:
            init_db()
            self._refresh_record_count()
        except sqlite3.Error as exc:
            self.status_label.config(
                text=f"Local database unavailable: {exc}", fg=ERROR_COLOR
            )

        self.name_entry.focus_set()

    # -- layout -----------------------------------------------------------

    def _place_window(self) -> None:
        width, height = 480, 680
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2 - 20)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self) -> None:
        shell = tk.Frame(self, bg=ROOT_BG, padx=28, pady=24)
        shell.pack(fill="both", expand=True)

        card = tk.Frame(
            shell,
            bg=CARD_BG,
            highlightbackground=BORDER_COLOR,
            highlightthickness=1,
        )
        card.pack(fill="both", expand=True)

        tk.Frame(card, bg=ACCENT_COLOR, height=6).pack(fill="x")

        body = tk.Frame(card, bg=CARD_BG, padx=30, pady=24)
        body.pack(fill="both", expand=True)

        tk.Label(
            body,
            text="WEEK 6  ·  INPUT VALIDATION",
            bg=CARD_BG,
            fg=ACCENT_COLOR,
            font=(FONT, 9, "bold"),
        ).pack(anchor="w")

        tk.Label(
            body,
            text="Registration Form",
            bg=CARD_BG,
            fg=TEXT_COLOR,
            font=(FONT, 22, "bold"),
        ).pack(anchor="w", pady=(2, 2))

        tk.Label(
            body,
            text="Every field is checked before your data is accepted.",
            bg=CARD_BG,
            fg=MUTED_COLOR,
            font=(FONT, 10),
        ).pack(anchor="w", pady=(0, 18))

        self.name_entry = self._add_field(
            body, "name", "Full Name", "Required - cannot be blank or only spaces"
        )
        self.age_entry = self._add_field(
            body, "age", "Age", "Whole number from 0 to 120"
        )
        self.email_entry = self._add_field(
            body, "email", "Email", "name@example.com"
        )

        self.submit_button = tk.Button(
            body,
            text="Submit registration",
            command=self.on_submit,
            bg=ACCENT_COLOR,
            fg="white",
            activebackground=ACCENT_HOVER,
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=(FONT, 11, "bold"),
        )
        self.submit_button.pack(fill="x", pady=(4, 10), ipady=8)
        self.submit_button.bind("<Enter>", self._on_button_enter)
        self.submit_button.bind("<Leave>", self._on_button_leave)

        self.status_label = tk.Label(
            body,
            text="",
            bg=CARD_BG,
            fg=ERROR_COLOR,
            font=(FONT, 10),
            justify="center",
            wraplength=350,
            height=2,
        )
        self.status_label.pack(fill="x")

        tk.Frame(body, bg="#EDF2EF", height=1).pack(fill="x", pady=(8, 10))

        self.record_count_label = tk.Label(
            body,
            text="",
            bg=CARD_BG,
            fg=MUTED_COLOR,
            font=(FONT, 9),
        )
        self.record_count_label.pack()

        tk.Label(
            body,
            text="Press Enter to submit",
            bg=CARD_BG,
            fg="#9AA5A0",
            font=(FONT, 8),
        ).pack(pady=(3, 0))

    def _add_field(
        self, parent: tk.Widget, key: str, label_text: str, hint_text: str
    ) -> tk.Entry:
        wrapper = tk.Frame(parent, bg=CARD_BG)
        wrapper.pack(fill="x", pady=(0, 13))

        tk.Label(
            wrapper,
            text=label_text,
            bg=CARD_BG,
            fg=TEXT_COLOR,
            font=(FONT, 10, "bold"),
        ).pack(anchor="w")

        entry = tk.Entry(
            wrapper,
            font=(FONT, 11),
            bg=FIELD_BG,
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=ACCENT_COLOR,
        )
        entry.pack(fill="x", pady=(5, 4), ipady=7)

        hint = tk.Label(
            wrapper,
            text=hint_text,
            bg=CARD_BG,
            fg=MUTED_COLOR,
            font=(FONT, 9),
            anchor="w",
        )
        hint.pack(anchor="w")

        error = tk.Label(
            wrapper,
            text="",
            bg=CARD_BG,
            fg=ERROR_COLOR,
            font=(FONT, 9),
            anchor="w",
            justify="left",
            wraplength=350,
        )

        self.fields[key] = {
            "entry": entry,
            "hint": hint,
            "hint_text": hint_text,
            "error": error,
        }

        if key == "email":
            entry.bind("<KeyRelease>", self.on_email_key_release)
        else:
            entry.bind(
                "<KeyRelease>",
                lambda event, field_key=key: self.on_field_key_release(field_key),
            )
        entry.bind("<FocusOut>", lambda event, field_key=key: self.on_focus_out(field_key))
        entry.bind("<Return>", self._on_return)
        return entry

    # -- validation feedback ---------------------------------------------

    def _set_field_error(self, key: str, message: str | None) -> None:
        field = self.fields[key]
        entry = field["entry"]
        hint = field["hint"]
        error = field["error"]
        assert isinstance(entry, tk.Entry)
        assert isinstance(hint, tk.Label)
        assert isinstance(error, tk.Label)

        if message:
            hint.pack_forget()
            error.config(text=message)
            error.pack(anchor="w")
            entry.config(highlightbackground=ERROR_COLOR, highlightcolor=ERROR_COLOR)
        else:
            error.config(text="")
            error.pack_forget()
            hint.pack(anchor="w")
            entry.config(highlightbackground=BORDER_COLOR, highlightcolor=ACCENT_COLOR)

    def _validate_one(self, key: str, value: str) -> str | None:
        if key == "name":
            return validate_required(value, "Full name")
        if key == "age":
            return validate_age(value)
        return validate_email(value)

    # -- event handlers ---------------------------------------------------

    def _on_return(self, event: tk.Event | None = None) -> str:
        self.on_submit()
        return "break"

    def _on_button_enter(self, event: tk.Event | None = None) -> None:
        self.submit_button.config(bg=ACCENT_HOVER)

    def _on_button_leave(self, event: tk.Event | None = None) -> None:
        self.submit_button.config(bg=ACCENT_COLOR)

    def on_email_key_release(self, event: tk.Event | None = None) -> None:
        """Live check for the optional real-time email validation."""
        self.status_label.config(text="")
        value = self.email_entry.get()
        if value.strip() == "" and not self.attempted_submit:
            self._set_field_error("email", None)
            return
        self._set_field_error("email", validate_email(value))

    def on_field_key_release(self, key: str) -> None:
        """Update name/age errors live only after a first submit attempt."""
        self.status_label.config(text="")
        if self.attempted_submit:
            value = self.fields[key]["entry"].get()  # type: ignore[union-attr]
            self._set_field_error(key, self._validate_one(key, value))

    def on_focus_out(self, key: str) -> None:
        """Check a field on blur once it has content (or after a submit)."""
        value = self.fields[key]["entry"].get()  # type: ignore[union-attr]
        if self.attempted_submit or value.strip():
            self._set_field_error(key, self._validate_one(key, value))

    def on_submit(self) -> None:
        """Validate every field, then save only a fully valid registration."""
        self.attempted_submit = True

        values = {
            key: self.fields[key]["entry"].get().strip()  # type: ignore[union-attr]
            for key in FIELD_ORDER
        }
        errors = validate_registration(values["name"], values["age"], values["email"])

        for key in FIELD_ORDER:
            self._set_field_error(key, errors[key])

        failing = [key for key in FIELD_ORDER if errors[key]]
        if failing:
            first_key = failing[0]
            self.status_label.config(text=errors[first_key], fg=ERROR_COLOR)
            entry = self.fields[first_key]["entry"]
            assert isinstance(entry, tk.Entry)
            entry.focus_set()
            entry.select_range(0, "end")
            return

        try:
            row_id = save_registration(values["name"], int(values["age"]), values["email"])
        except sqlite3.Error as exc:
            self.status_label.config(
                text=f"Could not save registration: {exc}", fg=ERROR_COLOR
            )
            return

        self.status_label.config(text="Registration successful!", fg=SUCCESS_COLOR)
        self._refresh_record_count(row_id)

    # -- database status --------------------------------------------------

    def _refresh_record_count(self, newest_row: int | None = None) -> None:
        try:
            count = count_registrations()
        except sqlite3.Error:
            self.record_count_label.config(text="Local database unavailable")
            return

        plural = "registration" if count == 1 else "registrations"
        text = f"{count} {plural} saved locally"
        if newest_row is not None:
            text += f"  ·  newest record #{newest_row}"
        self.record_count_label.config(text=text)


def main() -> None:
    app = RegistrationApp()
    app.mainloop()


if __name__ == "__main__":
    main()