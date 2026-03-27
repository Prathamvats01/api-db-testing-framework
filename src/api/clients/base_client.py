"""
base_client.py — Base HTTP client with retry logic, logging, and timing.

All API clients extend this. It uses a requests.Session so headers and
auth are set once and reused across all requests — exactly how a real
API automation framework works.

Features:
  - Automatic retry on 5xx / connection errors (configurable)
  - Response time assertion built-in
  - Full request/response logging to Allure
  - Raises on unexpected status codes (no silent failures)
"""

import time
import logging
from typing import Any

import allure
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.config import APIConfig

logger = logging.getLogger(__name__)


class BaseAPIClient:
    """
    Base HTTP client. Extend this for each API resource group.

    Usage:
        client = UsersClient()
        response = client.get("/users/1")
        assert response.status_code == 200
    """

    def __init__(self) -> None:
        self.base_url = APIConfig.BASE_URL
        self.session  = self._build_session()

    # ─────────────────────────────────────────────────────────────
    #  Core request methods
    # ─────────────────────────────────────────────────────────────

    def get(self, endpoint: str, params: dict | None = None,
            expected_status: int = 200, **kwargs) -> requests.Response:
        return self._request("GET", endpoint, params=params,
                             expected_status=expected_status, **kwargs)

    def post(self, endpoint: str, payload: dict | None = None,
             expected_status: int = 201, **kwargs) -> requests.Response:
        return self._request("POST", endpoint, json=payload,
                             expected_status=expected_status, **kwargs)

    def put(self, endpoint: str, payload: dict | None = None,
            expected_status: int = 200, **kwargs) -> requests.Response:
        return self._request("PUT", endpoint, json=payload,
                             expected_status=expected_status, **kwargs)

    def patch(self, endpoint: str, payload: dict | None = None,
              expected_status: int = 200, **kwargs) -> requests.Response:
        return self._request("PATCH", endpoint, json=payload,
                             expected_status=expected_status, **kwargs)

    def delete(self, endpoint: str,
               expected_status: int = 200, **kwargs) -> requests.Response:
        return self._request("DELETE", endpoint,
                             expected_status=expected_status, **kwargs)

    # ─────────────────────────────────────────────────────────────
    #  Internal
    # ─────────────────────────────────────────────────────────────

    def _request(self, method: str, endpoint: str,
                 expected_status: int | None = None, **kwargs) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        logger.info("→ %s %s", method, url)

        start_ms = time.perf_counter() * 1000
        response  = self.session.request(method, url,
                                         timeout=APIConfig.TIMEOUT_SECONDS, **kwargs)
        elapsed   = round(time.perf_counter() * 1000 - start_ms, 2)

        logger.info("← %s %s [%dms]", response.status_code, url, elapsed)

        # Attach full details to Allure
        self._attach_to_allure(method, url, kwargs, response, elapsed)

        # Assert status code if expected_status is specified
        if expected_status is not None:
            assert response.status_code == expected_status, (
                f"{method} {url} → expected {expected_status}, "
                f"got {response.status_code}\nBody: {response.text[:500]}"
            )

        # Store elapsed time for response time assertions
        response.elapsed_ms = elapsed  # type: ignore[attr-defined]
        return response

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            "Content-Type":  "application/json",
            "Accept":        "application/json",
            "User-Agent":    "API-DB-Testing-Framework/2.0",
        })

        # Retry on 5xx and connection errors
        retry_strategy = Retry(
            total              = APIConfig.MAX_RETRIES,
            backoff_factor     = APIConfig.RETRY_BACKOFF,
            status_forcelist   = [500, 502, 503, 504],
            allowed_methods    = ["GET", "POST", "PUT", "PATCH", "DELETE"],
            raise_on_status    = False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://",  adapter)
        return session

    def _attach_to_allure(self, method: str, url: str, kwargs: dict,
                           response: requests.Response, elapsed_ms: float) -> None:
        try:
            # Request body
            if payload := kwargs.get("json"):
                allure.attach(
                    str(payload), name=f"Request Body — {method}",
                    attachment_type=allure.attachment_type.JSON
                )

            # Response
            allure.attach(
                f"Status:  {response.status_code}\n"
                f"Time:    {elapsed_ms}ms\n"
                f"URL:     {url}\n\n"
                f"{response.text[:2000]}",
                name=f"Response — {response.status_code}",
                attachment_type=allure.attachment_type.TEXT,
            )
        except Exception:
            pass  # Never let reporting break tests
