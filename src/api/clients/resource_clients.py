"""
users_client.py — API client for /users endpoint.
posts_client.py — API client for /posts endpoint.
todos_client.py — API client for /todos endpoint.

All resource clients in one file for clarity.
"""

import requests
from src.api.clients.base_client import BaseAPIClient


class UsersClient(BaseAPIClient):
    """Client for JSONPlaceholder /users resource."""

    ENDPOINT = "/users"

    def get_all_users(self) -> requests.Response:
        return self.get(self.ENDPOINT)

    def get_user_by_id(self, user_id: int) -> requests.Response:
        return self.get(f"{self.ENDPOINT}/{user_id}")

    def get_user_not_found(self, user_id: int) -> requests.Response:
        """Expects 404 — use for negative tests."""
        return self.get(f"{self.ENDPOINT}/{user_id}", expected_status=404)

    def get_user_posts(self, user_id: int) -> requests.Response:
        return self.get(f"{self.ENDPOINT}/{user_id}/posts")

    def get_user_todos(self, user_id: int) -> requests.Response:
        return self.get(f"{self.ENDPOINT}/{user_id}/todos")

    def create_user(self, payload: dict) -> requests.Response:
        return self.post(self.ENDPOINT, payload=payload)

    def update_user(self, user_id: int, payload: dict) -> requests.Response:
        return self.put(f"{self.ENDPOINT}/{user_id}", payload=payload)

    def patch_user(self, user_id: int, payload: dict) -> requests.Response:
        return self.patch(f"{self.ENDPOINT}/{user_id}", payload=payload)

    def delete_user(self, user_id: int) -> requests.Response:
        return self.delete(f"{self.ENDPOINT}/{user_id}")


class PostsClient(BaseAPIClient):
    """Client for JSONPlaceholder /posts resource."""

    ENDPOINT = "/posts"

    def get_all_posts(self) -> requests.Response:
        return self.get(self.ENDPOINT)

    def get_post_by_id(self, post_id: int) -> requests.Response:
        return self.get(f"{self.ENDPOINT}/{post_id}")

    def get_posts_by_user(self, user_id: int) -> requests.Response:
        return self.get(self.ENDPOINT, params={"userId": user_id})

    def get_post_comments(self, post_id: int) -> requests.Response:
        return self.get(f"{self.ENDPOINT}/{post_id}/comments")

    def create_post(self, payload: dict) -> requests.Response:
        return self.post(self.ENDPOINT, payload=payload)

    def update_post(self, post_id: int, payload: dict) -> requests.Response:
        return self.put(f"{self.ENDPOINT}/{post_id}", payload=payload)

    def patch_post(self, post_id: int, payload: dict) -> requests.Response:
        return self.patch(f"{self.ENDPOINT}/{post_id}", payload=payload)

    def delete_post(self, post_id: int) -> requests.Response:
        return self.delete(f"{self.ENDPOINT}/{post_id}")


class TodosClient(BaseAPIClient):
    """Client for JSONPlaceholder /todos resource."""

    ENDPOINT = "/todos"

    def get_all_todos(self) -> requests.Response:
        return self.get(self.ENDPOINT)

    def get_todo_by_id(self, todo_id: int) -> requests.Response:
        return self.get(f"{self.ENDPOINT}/{todo_id}")

    def get_todos_by_user(self, user_id: int) -> requests.Response:
        return self.get(self.ENDPOINT, params={"userId": user_id})

    def get_completed_todos(self) -> requests.Response:
        return self.get(self.ENDPOINT, params={"completed": "true"})

    def create_todo(self, payload: dict) -> requests.Response:
        return self.post(self.ENDPOINT, payload=payload)

    def complete_todo(self, todo_id: int) -> requests.Response:
        return self.patch(f"{self.ENDPOINT}/{todo_id}",
                          payload={"completed": True})
