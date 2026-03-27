"""
test_posts_api.py — Posts + Comments API test suite against JSONPlaceholder.

Covers: CRUD for posts, comments as nested resource, schema contract,
        filtering by userId, response time SLA, negative paths.
"""

import allure
import pytest

from src.api.clients.resource_clients import PostsClient
from src.api.validators.response_validator import ResponseValidator
from config.config import APIConfig


@allure.epic("API Testing")
@allure.feature("Posts API")
class TestPostsAPI:

    # ── GET /posts ─────────────────────────────────────────────────

    @allure.story("Get All Posts")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    def test_get_all_posts_returns_100(self, posts_client: PostsClient) -> None:
        response = posts_client.get_all_posts()
        ResponseValidator(response) \
            .status_is(200) \
            .content_type_is_json() \
            .body_is_list() \
            .body_list_length_equals(100) \
            .validate()

    @allure.story("Get All Posts")
    @pytest.mark.regression
    def test_all_posts_have_required_fields(self, posts_client: PostsClient) -> None:
        posts = posts_client.get_all_posts().json()
        for post in posts:
            assert "id"     in post, "Post missing 'id'"
            assert "userId" in post, "Post missing 'userId'"
            assert "title"  in post, "Post missing 'title'"
            assert "body"   in post, "Post missing 'body'"

    # ── GET /posts/{id} ────────────────────────────────────────────

    @allure.story("Get Post By ID")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @pytest.mark.parametrize("post_id,expected_user_id", [(1, 1), (11, 2), (21, 3)])
    def test_get_post_by_id(
            self, posts_client: PostsClient,
            post_id: int, expected_user_id: int) -> None:
        response = posts_client.get_post_by_id(post_id)
        ResponseValidator(response) \
            .status_is(200) \
            .body_field_equals("id", post_id) \
            .body_field_equals("userId", expected_user_id) \
            .body_field_is_not_null("title") \
            .body_field_is_not_null("body") \
            .validate()

    @allure.story("Get Post By ID")
    @pytest.mark.regression
    def test_get_post_validates_schema(
            self, posts_client: PostsClient, post_schema: dict) -> None:
        response = posts_client.get_post_by_id(1)
        ResponseValidator(response) \
            .status_is(200) \
            .matches_schema(post_schema) \
            .validate()

    # ── GET /posts?userId= ─────────────────────────────────────────

    @allure.story("Filter Posts By User")
    @pytest.mark.regression
    def test_filter_posts_by_user_id(self, posts_client: PostsClient) -> None:
        response = posts_client.get_posts_by_user(user_id=1)
        ResponseValidator(response) \
            .status_is(200) \
            .body_is_list() \
            .body_list_not_empty() \
            .validate()
        posts = response.json()
        assert len(posts) == 10, f"User 1 should have 10 posts, got {len(posts)}"
        assert all(p["userId"] == 1 for p in posts), \
            "All returned posts should belong to user 1"

    # ── GET /posts/{id}/comments ───────────────────────────────────

    @allure.story("Post Comments")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.smoke
    def test_get_post_comments(
            self, posts_client: PostsClient, comment_schema: dict) -> None:
        response = posts_client.get_post_comments(post_id=1)
        ResponseValidator(response) \
            .status_is(200) \
            .body_is_list() \
            .body_list_not_empty() \
            .validate()

        comments = response.json()
        assert all(c["postId"] == 1 for c in comments), \
            "All comments should belong to post 1"
        # Validate first comment against schema
        ResponseValidator(posts_client.get_post_comments(1)) \
            .matches_schema({"type": "array",
                             "items": comment_schema}) \
            .validate()

    @allure.story("Post Comments")
    @pytest.mark.regression
    def test_all_comments_have_valid_emails(self, posts_client: PostsClient) -> None:
        comments = posts_client.get_post_comments(post_id=1).json()
        for comment in comments:
            assert "@" in comment.get("email", ""), \
                f"Invalid email in comment: {comment.get('email')}"

    # ── POST /posts ────────────────────────────────────────────────

    @allure.story("Create Post")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.regression
    def test_create_post_returns_201(
            self, posts_client: PostsClient, new_post_payload: dict) -> None:
        response = posts_client.create_post(new_post_payload)
        ResponseValidator(response) \
            .status_is(201) \
            .content_type_is_json() \
            .body_has_key("id") \
            .body_field_equals("userId", new_post_payload["userId"]) \
            .body_field_equals("title",  new_post_payload["title"]) \
            .validate()

    @allure.story("Create Post")
    @pytest.mark.regression
    def test_created_post_validates_schema(
            self, posts_client: PostsClient, new_post_payload: dict,
            schemas: dict) -> None:
        response = posts_client.create_post(new_post_payload)
        ResponseValidator(response) \
            .matches_schema(schemas["created_post_schema"]) \
            .validate()

    # ── PUT /posts/{id} ────────────────────────────────────────────

    @allure.story("Update Post")
    @pytest.mark.regression
    def test_update_post_returns_200(
            self, posts_client: PostsClient, update_post_payload: dict) -> None:
        response = posts_client.update_post(1, update_post_payload)
        ResponseValidator(response) \
            .status_is(200) \
            .body_field_equals("title", "Updated post title") \
            .body_field_equals("id", 1) \
            .validate()

    # ── PATCH /posts/{id} ──────────────────────────────────────────

    @allure.story("Patch Post")
    @pytest.mark.regression
    def test_patch_post_title_only(self, posts_client: PostsClient) -> None:
        response = posts_client.patch_post(1, {"title": "Patched title"})
        ResponseValidator(response) \
            .status_is(200) \
            .body_field_equals("title", "Patched title") \
            .validate()

    # ── DELETE /posts/{id} ─────────────────────────────────────────

    @allure.story("Delete Post")
    @pytest.mark.regression
    def test_delete_post_returns_200(self, posts_client: PostsClient) -> None:
        response = posts_client.delete_post(1)
        ResponseValidator(response).status_is(200).validate()

    # ── Negative ───────────────────────────────────────────────────

    @allure.story("Negative — Post Not Found")
    @pytest.mark.regression
    @pytest.mark.negative
    def test_get_nonexistent_post_returns_404(self, posts_client: PostsClient) -> None:
        response = posts_client.get(f"/posts/99999", expected_status=404)
        ResponseValidator(response).status_is(404).validate()

    # ── Performance ────────────────────────────────────────────────

    @allure.story("Performance SLA")
    @pytest.mark.performance
    @pytest.mark.regression
    def test_single_post_response_time_sla(self, posts_client: PostsClient) -> None:
        response = posts_client.get_post_by_id(1)
        elapsed  = getattr(response, "elapsed_ms",
                           response.elapsed.total_seconds() * 1000)
        assert elapsed < APIConfig.RESPONSE_TIME_P1, \
            f"GET /posts/1 took {elapsed:.0f}ms — exceeds SLA of {APIConfig.RESPONSE_TIME_P1}ms"
