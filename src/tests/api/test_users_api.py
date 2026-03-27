"""
test_users_api.py — Users API test suite against JSONPlaceholder.

Covers: GET (list, by ID, nested resources), POST, PUT, PATCH, DELETE,
        schema contract validation, response time SLA, negative paths.

Target: https://jsonplaceholder.typicode.com/users
"""

import allure
import pytest

from src.api.clients.resource_clients import UsersClient
from src.api.validators.response_validator import ResponseValidator
from config.config import APIConfig


@allure.epic("API Testing")
@allure.feature("Users API")
class TestUsersAPI:

    # ── GET /users ─────────────────────────────────────────────────

    @allure.story("Get All Users")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_get_all_users_returns_200(self, users_client: UsersClient) -> None:
        response = users_client.get_all_users()
        ResponseValidator(response) \
            .status_is(200) \
            .content_type_is_json() \
            .response_time_under(APIConfig.RESPONSE_TIME_P3) \
            .body_is_list() \
            .body_list_not_empty() \
            .validate()

    @allure.story("Get All Users")
    @pytest.mark.regression
    def test_get_all_users_returns_10_users(self, users_client: UsersClient) -> None:
        response = users_client.get_all_users()
        ResponseValidator(response) \
            .status_is(200) \
            .body_list_length_equals(10) \
            .validate()

    @allure.story("Get All Users")
    @pytest.mark.regression
    def test_all_users_have_required_fields(
            self, users_client: UsersClient, user_schema: dict) -> None:
        response = users_client.get_all_users()
        users    = response.json()

        # Validate each user object individually — not the full list
        for user in users:
            assert "id"       in user, f"Missing 'id' in user: {user}"
            assert "name"     in user, f"Missing 'name' in user: {user}"
            assert "username" in user, f"Missing 'username' in user: {user}"
            assert "email"    in user, f"Missing 'email' in user: {user}"

    # ── GET /users/{id} ────────────────────────────────────────────

    @allure.story("Get User By ID")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @pytest.mark.parametrize("user_id", [1, 5, 10])
    def test_get_user_by_id_returns_correct_user(
            self, users_client: UsersClient, user_id: int) -> None:
        response = users_client.get_user_by_id(user_id)
        ResponseValidator(response) \
            .status_is(200) \
            .content_type_is_json() \
            .response_time_under(APIConfig.RESPONSE_TIME_P3) \
            .body_has_keys("id", "name", "username", "email") \
            .body_field_equals("id", user_id) \
            .validate()
        

    @allure.story("Get User By ID")
    @pytest.mark.regression
    def test_get_user_validates_against_schema(
            self, users_client: UsersClient, user_schema: dict) -> None:
        response = users_client.get_user_by_id(1)
        ResponseValidator(response) \
            .status_is(200) \
            .matches_schema(user_schema) \
            .validate()

    @allure.story("Get User By ID")
    @pytest.mark.regression
    def test_get_user_email_is_not_empty(self, users_client: UsersClient) -> None:
        response = users_client.get_user_by_id(1)
        ResponseValidator(response) \
            .status_is(200) \
            .body_field_is_not_null("email") \
            .validate()
        user = response.json()
        assert "@" in user["email"], f"Email should be valid, got: {user['email']}"

    # ── Nested resources ───────────────────────────────────────────

    @allure.story("User Nested Resources")
    @pytest.mark.regression
    def test_get_user_posts_returns_list(self, users_client: UsersClient) -> None:
        response = users_client.get_user_posts(user_id=1)
        ResponseValidator(response) \
            .status_is(200) \
            .body_is_list() \
            .body_list_not_empty() \
            .validate()
        posts = response.json()
        assert all(p["userId"] == 1 for p in posts), \
            "All posts should belong to user 1"

    @allure.story("User Nested Resources")
    @pytest.mark.regression
    def test_get_user_todos_returns_list(self, users_client: UsersClient) -> None:
        response = users_client.get_user_todos(user_id=1)
        ResponseValidator(response) \
            .status_is(200) \
            .body_is_list() \
            .validate()

    # ── POST /users ────────────────────────────────────────────────

    @allure.story("Create User")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.regression
    def test_create_user_returns_201(self, users_client: UsersClient) -> None:
        payload  = {"name": "Pratham Vats", "username": "prathamvats",
                    "email": "prathamvats94@gmail.com"}
        response = users_client.create_user(payload)
        ResponseValidator(response) \
            .status_is(201) \
            .content_type_is_json() \
            .body_has_key("id") \
            .body_field_equals("name", "Pratham Vats") \
            .body_field_equals("email", "prathamvats94@gmail.com") \
            .validate()

    @allure.story("Create User")
    @pytest.mark.regression
    def test_created_user_id_is_auto_assigned(self, users_client: UsersClient) -> None:
        payload  = {"name": "Test User", "username": "testuser",
                    "email": "test@example.com"}
        response = users_client.create_user(payload)
        user_id  = response.json().get("id")
        assert user_id is not None, "Created user should have an auto-assigned ID"
        assert isinstance(user_id, int), f"ID should be an integer, got: {type(user_id)}"

    # ── PUT /users/{id} ────────────────────────────────────────────

    @allure.story("Update User")
    @pytest.mark.regression
    def test_update_user_returns_200(self, users_client: UsersClient) -> None:
        payload  = {"id": 1, "name": "Updated Name",
                    "username": "updateduser", "email": "updated@test.com"}
        response = users_client.update_user(1, payload)
        ResponseValidator(response) \
            .status_is(200) \
            .body_field_equals("name", "Updated Name") \
            .validate()

    # ── PATCH /users/{id} ──────────────────────────────────────────

    @allure.story("Patch User")
    @pytest.mark.regression
    def test_patch_user_email_only(self, users_client: UsersClient) -> None:
        response = users_client.patch_user(1, {"email": "patched@example.com"})
        ResponseValidator(response) \
            .status_is(200) \
            .body_field_equals("email", "patched@example.com") \
            .validate()

    # ── DELETE /users/{id} ─────────────────────────────────────────

    @allure.story("Delete User")
    @pytest.mark.regression
    def test_delete_user_returns_200(self, users_client: UsersClient) -> None:
        response = users_client.delete_user(1)
        ResponseValidator(response) \
            .status_is(200) \
            .validate()

    # ── Negative tests ─────────────────────────────────────────────

    @allure.story("Negative — User Not Found")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.regression
    @pytest.mark.negative
    def test_get_nonexistent_user_returns_404(self, users_client: UsersClient) -> None:
        response = users_client.get_user_not_found(9999)
        ResponseValidator(response) \
            .status_is(404) \
            .validate()

    # ── Response time SLA ──────────────────────────────────────────

    @allure.story("Performance SLA")
    @pytest.mark.regression
    @pytest.mark.performance
    def test_users_list_response_time_sla(self, users_client: UsersClient) -> None:
        response = users_client.get_all_users()
        elapsed  = getattr(response, "elapsed_ms",
                           response.elapsed.total_seconds() * 1000)
        assert elapsed < APIConfig.RESPONSE_TIME_P3, \
            f"GET /users took {elapsed:.0f}ms — exceeds SLA of {APIConfig.RESPONSE_TIME_P3}ms"
