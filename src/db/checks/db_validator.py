"""
db_validator.py — Reusable database validation checks.

All checks return a ValidationResult — never raise by themselves.
Test functions decide whether to assert on them. This keeps the
check logic and test assertion logic cleanly separated.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from src.db.connector.db_connector import DBConnector

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Immutable result of a single DB check."""
    check_name: str
    table:      str
    passed:     bool
    message:    str
    details:    dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        icon = "✔" if self.passed else "✗"
        return f"{icon} [{self.table}] {self.check_name}: {self.message}"


class DBValidator:
    """
    Database validation checks targeting the seeded PostgreSQL database.

    Every method returns a ValidationResult — call assert_passed()
    in tests to turn failures into test failures with clear messages.
    """

    def __init__(self) -> None:
        self._db = DBConnector.get_instance()

    # ─────────────────────────────────────────────────────────────
    #  Row count checks
    # ─────────────────────────────────────────────────────────────

    def check_row_count(self, table: str, expected_min: int,
                        expected_max: int | None = None) -> ValidationResult:
        """Verify table has rows within expected bounds."""
        actual = self._db.get_row_count(table)
        check  = "row_count"

        if actual < expected_min:
            return ValidationResult(check, table, False,
                f"Row count {actual} is below minimum {expected_min}",
                {"actual": actual, "expected_min": expected_min})

        if expected_max is not None and actual > expected_max:
            return ValidationResult(check, table, False,
                f"Row count {actual} exceeds maximum {expected_max}",
                {"actual": actual, "expected_max": expected_max})

        return ValidationResult(check, table, True,
            f"Row count {actual} is within expected range",
            {"actual": actual, "expected_min": expected_min})

    # ─────────────────────────────────────────────────────────────
    #  Null checks
    # ─────────────────────────────────────────────────────────────

    def check_no_nulls(self, table: str, column: str) -> ValidationResult:
        """Verify a column has zero NULL values."""
        null_count = self._db.execute_scalar(
            f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL"  # noqa: S608
        )
        check = f"null_check:{column}"

        if null_count and null_count > 0:
            sample = self._db.execute(
                f"SELECT * FROM {table} WHERE {column} IS NULL LIMIT 3"  # noqa: S608
            )
            return ValidationResult(check, table, False,
                f"Column '{column}' has {null_count} NULL value(s)",
                {"null_count": null_count, "sample_rows": sample})

        return ValidationResult(check, table, True,
            f"Column '{column}': no NULLs found ✓",
            {"null_count": 0})

    def check_null_rate(self, table: str, column: str,
                        max_null_rate: float = 0.05) -> ValidationResult:
        """Verify null rate in a column is below threshold."""
        total = self._db.get_row_count(table)
        if total == 0:
            return ValidationResult(f"null_rate:{column}", table, True, "Table is empty")

        null_count = self._db.execute_scalar(
            f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL"  # noqa: S608
        ) or 0
        rate = null_count / total

        passed = rate <= max_null_rate
        return ValidationResult(
            f"null_rate:{column}", table, passed,
            f"Column '{column}' null rate: {rate:.1%} "
            f"({'≤' if passed else '>'} threshold {max_null_rate:.1%})",
            {"null_count": null_count, "total": total, "rate": rate}
        )

    # ─────────────────────────────────────────────────────────────
    #  Uniqueness / duplicate checks
    # ─────────────────────────────────────────────────────────────

    def check_unique(self, table: str, column: str) -> ValidationResult:
        """Verify a column has no duplicate values."""
        result = self._db.execute(f"""
            SELECT {column}, COUNT(*) AS cnt
            FROM   {table}
            GROUP  BY {column}
            HAVING COUNT(*) > 1
            LIMIT  5
        """)  # noqa: S608
        check = f"unique_check:{column}"

        if result:
            return ValidationResult(check, table, False,
                f"Column '{column}' has {len(result)} duplicate value(s)",
                {"duplicates": result})

        return ValidationResult(check, table, True,
            f"Column '{column}' is unique across all rows ✓")

    # ─────────────────────────────────────────────────────────────
    #  Referential integrity / FK checks
    # ─────────────────────────────────────────────────────────────

    def check_referential_integrity(
            self,
            child_table:   str,
            child_column:  str,
            parent_table:  str,
            parent_column: str
    ) -> ValidationResult:
        """Detect orphaned rows in child table."""
        orphans = self._db.execute(f"""
            SELECT DISTINCT c.{child_column}
            FROM   {child_table} c
            LEFT   JOIN {parent_table} p ON c.{child_column} = p.{parent_column}
            WHERE  p.{parent_column} IS NULL
            LIMIT  10
        """)  # noqa: S608
        check = f"fk:{child_table}.{child_column}→{parent_table}.{parent_column}"

        if orphans:
            orphan_keys = [list(row.values())[0] for row in orphans]
            return ValidationResult(check, child_table, False,
                f"{len(orphans)} orphaned key(s) in {child_table}.{child_column} "
                f"referencing {parent_table}.{parent_column}",
                {"orphan_keys": orphan_keys})

        return ValidationResult(check, child_table, True,
            f"All {child_table}.{child_column} keys exist in {parent_table}.{parent_column} ✓")

    # ─────────────────────────────────────────────────────────────
    #  Data type / format checks
    # ─────────────────────────────────────────────────────────────

    def check_email_format(self, table: str, column: str) -> ValidationResult:
        """Verify all non-null email addresses match a basic email pattern."""
        invalid = self._db.execute(f"""
            SELECT {column}
            FROM   {table}
            WHERE  {column} IS NOT NULL
              AND  {column} !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{{2,}}$'
            LIMIT  5
        """)  # noqa: S608
        check = f"email_format:{column}"

        if invalid:
            return ValidationResult(check, table, False,
                f"{len(invalid)} invalid email(s) in column '{column}'",
                {"invalid_emails": [list(r.values())[0] for r in invalid]})

        return ValidationResult(check, table, True,
            f"All emails in column '{column}' match expected format ✓")

    def check_value_range(self, table: str, column: str,
                          min_val: int | float | None = None,
                          max_val: int | float | None = None) -> ValidationResult:
        """Verify numeric column values fall within expected range."""
        conditions = []
        if min_val is not None:
            conditions.append(f"{column} < {min_val}")
        if max_val is not None:
            conditions.append(f"{column} > {max_val}")

        if not conditions:
            return ValidationResult(f"value_range:{column}", table, True,
                "No range bounds specified — skipped")

        where = " OR ".join(conditions)
        violations = self._db.execute_scalar(
            f"SELECT COUNT(*) FROM {table} WHERE {where}"  # noqa: S608
        ) or 0

        check = f"value_range:{column}"
        if violations > 0:
            return ValidationResult(check, table, False,
                f"Column '{column}' has {violations} value(s) outside "
                f"range [{min_val}, {max_val}]",
                {"violations": violations, "min": min_val, "max": max_val})

        return ValidationResult(check, table, True,
            f"All values in '{column}' within range [{min_val}, {max_val}] ✓")

    # ─────────────────────────────────────────────────────────────
    #  Table existence check
    # ─────────────────────────────────────────────────────────────

    def check_table_exists(self, table: str) -> ValidationResult:
        exists = self._db.table_exists(table)
        return ValidationResult(
            "table_exists", table, exists,
            f"Table '{table}' {'exists ✓' if exists else 'does NOT exist ✗'}"
        )

    # ─────────────────────────────────────────────────────────────
    #  Assertion helper
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def assert_passed(result: ValidationResult) -> None:
        """Assert that a validation result passed. Used in test functions."""
        assert result.passed, str(result)
