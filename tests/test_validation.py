"""Automated tests for the Week 6 registration form."""

from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

import registration_form as rf  # noqa: E402


class ValidationFunctionTests(unittest.TestCase):
    def test_required_rejects_blank_and_spaces(self) -> None:
        self.assertEqual(
            rf.validate_required("", "Full name"), "Full name is required."
        )
        self.assertEqual(
            rf.validate_required("   ", "Full name"), "Full name is required."
        )
        self.assertIsNone(rf.validate_required("Alex Morgan", "Full name"))

    def test_age_accepts_boundaries(self) -> None:
        for value in ("0", "120", "21", " 21 "):
            with self.subTest(value=value):
                self.assertIsNone(rf.validate_age(value))

    def test_age_rejects_non_numbers(self) -> None:
        for value in ("", "abc", "21.5", "twenty-one"):
            with self.subTest(value=value):
                self.assertEqual(
                    rf.validate_age(value), "Age must be a whole number."
                )

    def test_age_rejects_out_of_range(self) -> None:
        for value in ("-5", "-1", "121", "200"):
            with self.subTest(value=value):
                self.assertEqual(
                    rf.validate_age(value), "Age must be between 0 and 120."
                )

    def test_email_accepts_valid_addresses(self) -> None:
        for value in (
            "alex@example.com",
            "alex.morgan@university.ac.uk",
            "  alex@example.com  ",
        ):
            with self.subTest(value=value):
                self.assertIsNone(rf.validate_email(value))

    def test_email_rejects_invalid_addresses(self) -> None:
        invalid = {
            "": "Email is required.",
            "   ": "Email is required.",
            "john.example.com": "Enter a valid email address, e.g. name@example.com",
            "john@example": "Enter a valid email address, e.g. name@example.com",
            "john @example.com": "Enter a valid email address, e.g. name@example.com",
            "john@@example.com": "Enter a valid email address, e.g. name@example.com",
        }
        for value, expected in invalid.items():
            with self.subTest(value=value):
                self.assertEqual(rf.validate_email(value), expected)

    def test_all_blank_reports_first_error_in_order(self) -> None:
        errors = rf.validate_registration("", "", "")
        self.assertEqual(errors["name"], "Full name is required.")
        self.assertEqual(errors["age"], "Age must be a whole number.")
        self.assertEqual(errors["email"], "Email is required.")


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = rf.DB_PATH
        rf.DB_PATH = Path(self.temp_dir.name) / "test_registrations.db"
        rf.init_db()

    def tearDown(self) -> None:
        rf.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_save_and_count_registration(self) -> None:
        self.assertEqual(rf.count_registrations(), 0)
        row_id = rf.save_registration("Alex Morgan", 21, "alex@example.com")
        self.assertEqual(rf.count_registrations(), 1)

        with closing(sqlite3.connect(rf.DB_PATH)) as conn:
            row = conn.execute(
                "SELECT name, age, email FROM registrations WHERE id = ?",
                (row_id,),
            ).fetchone()
        self.assertEqual(row, ("Alex Morgan", 21, "alex@example.com"))


class RegistrationAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = rf.DB_PATH
        rf.DB_PATH = Path(self.temp_dir.name) / "gui_test.db"
        self.app = rf.RegistrationApp()
        self.app.withdraw()

    def tearDown(self) -> None:
        self.app.destroy()
        rf.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def _set_values(self, name: str, age: str, email: str) -> None:
        for entry, value in (
            (self.app.name_entry, name),
            (self.app.age_entry, age),
            (self.app.email_entry, email),
        ):
            entry.delete(0, "end")
            entry.insert(0, value)

    def _inline_errors(self) -> dict[str, str]:
        return {
            key: self.app.fields[key]["error"].cget("text")  # type: ignore[union-attr]
            for key in rf.FIELD_ORDER
        }

    def test_all_blank_shows_first_error_and_no_database_row(self) -> None:
        self._set_values("", "", "")
        self.app.on_submit()

        self.assertEqual(
            self.app.status_label.cget("text"), "Full name is required."
        )
        self.assertEqual(self.app.status_label.cget("fg"), rf.ERROR_COLOR)
        self.assertEqual(
            self._inline_errors(),
            {
                "name": "Full name is required.",
                "age": "Age must be a whole number.",
                "email": "Email is required.",
            },
        )
        self.assertEqual(rf.count_registrations(), 0)

    def test_age_errors_are_shown_inline(self) -> None:
        self._set_values("Alex Morgan", "abc", "alex@example.com")
        self.app.on_submit()
        self.assertEqual(
            self.app.status_label.cget("text"), "Age must be a whole number."
        )
        self.assertEqual(
            self._inline_errors()["age"], "Age must be a whole number."
        )

        self._set_values("Alex Morgan", "200", "alex@example.com")
        self.app.on_submit()
        self.assertEqual(
            self.app.status_label.cget("text"),
            "Age must be between 0 and 120.",
        )
        self.assertEqual(rf.count_registrations(), 0)

    def test_malformed_email_is_rejected(self) -> None:
        self._set_values("Alex Morgan", "21", "john @example.com")
        self.app.on_submit()
        self.assertEqual(
            self.app.status_label.cget("text"),
            "Enter a valid email address, e.g. name@example.com",
        )
        self.assertEqual(rf.count_registrations(), 0)

    def test_valid_submission_shows_success_and_saves_row(self) -> None:
        self._set_values("Alex Morgan", "21", "alex@example.com")
        self.app.on_submit()

        self.assertEqual(
            self.app.status_label.cget("text"), "Registration successful!"
        )
        self.assertEqual(self.app.status_label.cget("fg"), rf.SUCCESS_COLOR)
        self.assertEqual(rf.count_registrations(), 1)
        self.assertIn("1 registration saved locally", self.app.record_count_label.cget("text"))

    def test_live_email_validation_updates_immediately(self) -> None:
        self._set_values("Alex Morgan", "21", "john.example.com")
        self.app.on_email_key_release()
        self.assertEqual(
            self._inline_errors()["email"],
            "Enter a valid email address, e.g. name@example.com",
        )

        self._set_values("Alex Morgan", "21", "john@example")
        self.app.on_email_key_release()
        self.assertNotEqual(self._inline_errors()["email"], "")

        self._set_values("Alex Morgan", "21", "john@example.com")
        self.app.on_email_key_release()
        self.assertEqual(self._inline_errors()["email"], "")


if __name__ == "__main__":
    unittest.main(verbosity=2)