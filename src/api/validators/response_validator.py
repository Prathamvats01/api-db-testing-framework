"""
response_validator.py — Reusable response assertion library.

All API tests call these validators rather than writing raw asserts.
This means if the API changes its response format, you update one place.
"""

import jsonschema
import logging
from typing import Any
from config.config import APIConfig

logger = logging.getLogger(__name__)


class ResponseValidator:
    """
    Fluent validator for HTTP responses.

    Usage:
        ResponseValidator(response)
            .status_is(200)
            .content_type_is_json()
            .response_time_under(2000)
            .body_has_key("id")
            .validate()
    """

    def __init__(self, response: Any) -> None:
        self._response = response
        self._errors:   list[str] = []

    # ─────────────────────────────────────────────────────────────
    #  Status code assertions
    # ─────────────────────────────────────────────────────────────

    def status_is(self, expected: int) -> "ResponseValidator":
        actual = self._response.status_code
        if actual != expected:
            self._errors.append(
                f"Status: expected {expected}, got {actual}")
        return self

    def status_is_success(self) -> "ResponseValidator":
        code = self._response.status_code
        if not (200 <= code < 300):
            self._errors.append(f"Expected 2xx status, got {code}")
        return self

    # ─────────────────────────────────────────────────────────────
    #  Header assertions
    # ─────────────────────────────────────────────────────────────

    def content_type_is_json(self) -> "ResponseValidator":
        ct = self._response.headers.get("Content-Type", "")
        if "application/json" not in ct:
            self._errors.append(f"Content-Type: expected JSON, got '{ct}'")
        return self

    def has_header(self, header_name: str) -> "ResponseValidator":
        if header_name not in self._response.headers:
            self._errors.append(f"Missing header: {header_name}")
        return self

    # ─────────────────────────────────────────────────────────────
    #  Response time assertions
    # ─────────────────────────────────────────────────────────────

    def response_time_under(self, max_ms: int) -> "ResponseValidator":
        actual = getattr(self._response, "elapsed_ms",
                         self._response.elapsed.total_seconds() * 1000)
        if actual > max_ms:
            self._errors.append(
                f"Response time: {actual:.0f}ms exceeded limit of {max_ms}ms")
        return self

    def response_time_under_sla(self) -> "ResponseValidator":
        return self.response_time_under(APIConfig.RESPONSE_TIME_P2)

    # ─────────────────────────────────────────────────────────────
    #  Body assertions
    # ─────────────────────────────────────────────────────────────

    def body_has_key(self, key: str) -> "ResponseValidator":
        body = self._response.json()
        if isinstance(body, dict) and key not in body:
            self._errors.append(f"Response body missing key: '{key}'")
        return self

    def body_has_keys(self, *keys: str) -> "ResponseValidator":
        for key in keys:
            self.body_has_key(key)
        return self

    def body_field_equals(self, key: str, expected: Any) -> "ResponseValidator":
        body = self._response.json()
        actual = body.get(key)
        if actual != expected:
            self._errors.append(
                f"Field '{key}': expected {expected!r}, got {actual!r}")
        return self

    def body_field_is_not_null(self, key: str) -> "ResponseValidator":
        body = self._response.json()
        if body.get(key) is None:
            self._errors.append(f"Field '{key}' is null or missing")
        return self

    def body_is_list(self) -> "ResponseValidator":
        body = self._response.json()
        if not isinstance(body, list):
            self._errors.append(
                f"Response body should be a list, got {type(body).__name__}")
        return self

    def body_list_length_equals(self, expected: int) -> "ResponseValidator":
        body = self._response.json()
        if isinstance(body, list) and len(body) != expected:
            self._errors.append(
                f"List length: expected {expected}, got {len(body)}")
        return self

    def body_list_not_empty(self) -> "ResponseValidator":
        body = self._response.json()
        if isinstance(body, list) and len(body) == 0:
            self._errors.append("Response body list should not be empty")
        return self

    def matches_schema(self, schema: dict) -> "ResponseValidator":
        """Validate response body against a JSON Schema."""
        try:
            jsonschema.validate(instance=self._response.json(), schema=schema)
        except jsonschema.ValidationError as e:
            self._errors.append(f"Schema validation failed: {e.message}")
        return self

    # ─────────────────────────────────────────────────────────────
    #  Terminal — execute all assertions
    # ─────────────────────────────────────────────────────────────

    def validate(self) -> "ResponseValidator":
        """Raise AssertionError with ALL failures if any exist."""
        if self._errors:
            error_summary = "\n  ✗ ".join(self._errors)
            raise AssertionError(
                f"Response validation failed ({len(self._errors)} issue(s)):\n"
                f"  ✗ {error_summary}"
            )
        logger.debug("✔ Response validation passed")
        return self

    def get_json(self) -> Any:
        return self._response.json()
