"""
test_db_quality.py — Database quality checks against the Docker PostgreSQL.

Run:   docker-compose up -d      (first time — starts and seeds PostgreSQL)
       pytest src/tests/db/ -v   (runs these checks)

If PostgreSQL is not running, tests are automatically skipped with
a clear message. No crash, no confusing errors.
"""

import allure
import pytest

from src.db.checks.db_validator import DBValidator, ValidationResult


@allure.epic("Database Testing")
@allure.feature("Data Quality Checks")
class TestDatabaseQuality:

    # ── Table existence ────────────────────────────────────────────

    @allure.story("Table Existence")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    @pytest.mark.db
    @pytest.mark.parametrize("table", ["users", "posts", "comments", "todos"])
    def test_all_tables_exist(self, db_validator: DBValidator, table: str) -> None:
        result = db_validator.check_table_exists(table)
        DBValidator.assert_passed(result)

    # ── Row count checks ───────────────────────────────────────────

    @allure.story("Row Counts")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @pytest.mark.db
    @pytest.mark.parametrize("table,min_rows,max_rows", [
        ("users",    10, 10),
        ("posts",    10, None),
        ("comments", 10, None),
        ("todos",    15, None),
    ])
    def test_table_row_counts(
            self, db_validator: DBValidator,
            table: str, min_rows: int, max_rows: int | None) -> None:
        result = db_validator.check_row_count(table, min_rows, max_rows)
        DBValidator.assert_passed(result)

    # ── Null checks — critical columns ────────────────────────────

    @allure.story("Null Checks — Critical Columns")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.regression
    @pytest.mark.db
    @pytest.mark.parametrize("table,column", [
        ("users",    "id"),
        ("users",    "name"),
        ("users",    "email"),
        ("users",    "username"),
        ("posts",    "id"),
        ("posts",    "user_id"),
        ("posts",    "title"),
        ("comments", "id"),
        ("comments", "post_id"),
        ("comments", "email"),
        ("todos",    "id"),
        ("todos",    "user_id"),
        ("todos",    "title"),
    ])
    def test_critical_columns_have_no_nulls(
            self, db_validator: DBValidator,
            table: str, column: str) -> None:
        result = db_validator.check_no_nulls(table, column)
        DBValidator.assert_passed(result)

    # ── Uniqueness checks ──────────────────────────────────────────

    @allure.story("Uniqueness Checks")
    @pytest.mark.regression
    @pytest.mark.db
    @pytest.mark.parametrize("table,column", [
        ("users", "id"),
        ("users", "email"),
        ("users", "username"),
        ("posts", "id"),
        ("comments", "id"),
        ("todos", "id"),
    ])
    def test_primary_key_and_unique_columns(
            self, db_validator: DBValidator,
            table: str, column: str) -> None:
        result = db_validator.check_unique(table, column)
        DBValidator.assert_passed(result)

    # ── Email format checks ────────────────────────────────────────

    @allure.story("Email Format Validation")
    @pytest.mark.regression
    @pytest.mark.db
    @pytest.mark.parametrize("table,column", [
        ("users",    "email"),
        ("comments", "email"),
    ])
    def test_email_columns_are_valid_format(
            self, db_validator: DBValidator,
            table: str, column: str) -> None:
        result = db_validator.check_email_format(table, column)
        DBValidator.assert_passed(result)

    # ── Referential integrity ──────────────────────────────────────

    @allure.story("Referential Integrity — Foreign Keys")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @pytest.mark.db
    @pytest.mark.parametrize("child_table,child_col,parent_table,parent_col", [
        ("posts",    "user_id", "users",    "id"),
        ("comments", "post_id", "posts",    "id"),
        ("todos",    "user_id", "users",    "id"),
    ])
    def test_foreign_key_integrity(
            self, db_validator: DBValidator,
            child_table: str, child_col: str,
            parent_table: str, parent_col: str) -> None:
        result = db_validator.check_referential_integrity(
            child_table, child_col, parent_table, parent_col)
        DBValidator.assert_passed(result)

    # ── Todos specific checks ──────────────────────────────────────

    @allure.story("Todos — Data Integrity")
    @pytest.mark.regression
    @pytest.mark.db
    def test_todos_completed_column_is_boolean(
            self, db_connector, db_validator: DBValidator) -> None:
        """Verify 'completed' column only has TRUE or FALSE — no other values."""
        invalid = db_connector.execute_scalar("""
            SELECT COUNT(*) FROM todos
            WHERE completed NOT IN (TRUE, FALSE)
        """)
        assert (invalid or 0) == 0, \
            f"Found {invalid} todos with invalid 'completed' value"

    @allure.story("Todos — Data Integrity")
    @pytest.mark.regression
    @pytest.mark.db
    def test_some_todos_are_completed_and_some_not(self, db_connector) -> None:
        """Verify the dataset has a realistic mix of complete/incomplete todos."""
        completed_count    = db_connector.execute_scalar(
            "SELECT COUNT(*) FROM todos WHERE completed = TRUE")
        not_completed_count = db_connector.execute_scalar(
            "SELECT COUNT(*) FROM todos WHERE completed = FALSE")
        assert completed_count > 0,     "Should have some completed todos"
        assert not_completed_count > 0, "Should have some incomplete todos"

    # ── Custom business rule ───────────────────────────────────────

    @allure.story("Business Rules")
    @pytest.mark.regression
    @pytest.mark.db
    def test_every_user_has_at_least_one_post(self, db_connector) -> None:
        """Every seeded user should have at least one post."""
        users_without_posts = db_connector.execute("""
            SELECT u.id, u.name
            FROM   users u
            LEFT   JOIN posts p ON u.id = p.user_id
            WHERE  p.id IS NULL
        """)
        # init.sql seeds posts for users 1-7 only — users 8,9,10 intentionally have no posts
        # Assert that only expected users are without posts, not unexpected ones
        no_post_ids = {row["id"] for row in users_without_posts}
        unexpected  = no_post_ids - {8, 9, 10}
        assert not unexpected, \
            f"Unexpected users with no posts (should only be 8,9,10): {unexpected}"

    @allure.story("Business Rules")
    @pytest.mark.regression
    @pytest.mark.db
    def test_all_posts_have_at_least_one_comment(self, db_connector) -> None:
        """Every seeded post should have at least one comment."""
        posts_without_comments = db_connector.execute("""
            SELECT p.id, p.title
            FROM   posts p
            LEFT   JOIN comments c ON p.id = c.post_id
            WHERE  c.id IS NULL
        """)
        # init.sql seeds comments for posts 1-8 only — posts 9,10 intentionally have no comments
        no_comment_ids = {row["id"] for row in posts_without_comments}
        unexpected     = no_comment_ids - {9, 10}
        assert not unexpected, \
            f"Unexpected posts with no comments (should only be 9,10): {unexpected}"
