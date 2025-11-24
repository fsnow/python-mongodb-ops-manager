# Copyright 2024 Frank Snow
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Exception hierarchy for MongoDB Ops Manager API client.

All exceptions inherit from OpsManagerError, allowing callers to catch
all API-related errors with a single except clause if desired.
"""

from typing import Any, Dict, Optional


class OpsManagerError(Exception):
    """Base exception for all Ops Manager API errors.

    Attributes:
        message: Human-readable error message.
        status_code: HTTP status code from the API response (if applicable).
        error_code: Ops Manager error code from the response (if applicable).
        detail: Detailed error message from the API response.
        response: Raw response data from the API.
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        detail: Optional[str] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.detail = detail
        self.response = response or {}

    def __str__(self) -> str:
        parts = [self.message]
        if self.error_code:
            parts.append(f"[{self.error_code}]")
        if self.detail:
            parts.append(f"- {self.detail}")
        return " ".join(parts)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code}, "
            f"error_code={self.error_code!r})"
        )


class OpsManagerAuthenticationError(OpsManagerError):
    """Authentication failed (HTTP 401).

    Raised when API credentials are invalid or missing.
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        error_code: Optional[str] = None,
        detail: Optional[str] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=401,
            error_code=error_code,
            detail=detail,
            response=response,
        )


class OpsManagerForbiddenError(OpsManagerError):
    """Access forbidden (HTTP 403).

    Raised when the authenticated user lacks permission for the requested resource.
    """

    def __init__(
        self,
        message: str = "Access forbidden",
        error_code: Optional[str] = None,
        detail: Optional[str] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=403,
            error_code=error_code,
            detail=detail,
            response=response,
        )


class OpsManagerNotFoundError(OpsManagerError):
    """Resource not found (HTTP 404).

    Raised when the requested resource does not exist.
    """

    def __init__(
        self,
        message: str = "Resource not found",
        error_code: Optional[str] = None,
        detail: Optional[str] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=404,
            error_code=error_code,
            detail=detail,
            response=response,
        )


class OpsManagerBadRequestError(OpsManagerError):
    """Bad request (HTTP 400).

    Raised when the request is malformed or contains invalid parameters.
    """

    def __init__(
        self,
        message: str = "Bad request",
        error_code: Optional[str] = None,
        detail: Optional[str] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code=error_code,
            detail=detail,
            response=response,
        )


class OpsManagerConflictError(OpsManagerError):
    """Conflict (HTTP 409).

    Raised when the request conflicts with the current state of the resource,
    such as attempting to create a resource that already exists.
    """

    def __init__(
        self,
        message: str = "Conflict",
        error_code: Optional[str] = None,
        detail: Optional[str] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=409,
            error_code=error_code,
            detail=detail,
            response=response,
        )


class OpsManagerRateLimitError(OpsManagerError):
    """Rate limit exceeded (HTTP 429).

    Raised when too many requests have been made in a given time period.

    Attributes:
        retry_after: Seconds to wait before retrying (if provided by API).
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        error_code: Optional[str] = None,
        detail: Optional[str] = None,
        response: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
    ):
        super().__init__(
            message=message,
            status_code=429,
            error_code=error_code,
            detail=detail,
            response=response,
        )
        self.retry_after = retry_after


class OpsManagerServerError(OpsManagerError):
    """Server error (HTTP 5xx).

    Raised when the Ops Manager server encounters an internal error.
    """

    def __init__(
        self,
        message: str = "Server error",
        status_code: int = 500,
        error_code: Optional[str] = None,
        detail: Optional[str] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status_code,
            error_code=error_code,
            detail=detail,
            response=response,
        )


class OpsManagerTimeoutError(OpsManagerError):
    """Request timeout.

    Raised when a request to the Ops Manager API times out.
    """

    def __init__(
        self,
        message: str = "Request timed out",
        detail: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            detail=detail,
        )


class OpsManagerConnectionError(OpsManagerError):
    """Connection error.

    Raised when unable to connect to the Ops Manager API.
    """

    def __init__(
        self,
        message: str = "Connection failed",
        detail: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            detail=detail,
        )


class OpsManagerValidationError(OpsManagerError):
    """Client-side validation error.

    Raised when input validation fails before making an API request.
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
    ):
        detail = f"Invalid value for field: {field}" if field else None
        super().__init__(
            message=message,
            detail=detail,
        )
        self.field = field


def raise_for_status(status_code: int, response_data: Dict[str, Any]) -> None:
    """Raise an appropriate exception based on HTTP status code.

    Args:
        status_code: HTTP status code from the response.
        response_data: Parsed JSON response body.

    Raises:
        OpsManagerError: Appropriate subclass based on status code.
    """
    if 200 <= status_code < 300:
        return

    error_code = response_data.get("errorCode")
    detail = response_data.get("detail")
    reason = response_data.get("reason", "")

    error_classes = {
        400: OpsManagerBadRequestError,
        401: OpsManagerAuthenticationError,
        403: OpsManagerForbiddenError,
        404: OpsManagerNotFoundError,
        409: OpsManagerConflictError,
        429: OpsManagerRateLimitError,
    }

    if status_code in error_classes:
        raise error_classes[status_code](
            message=reason or error_classes[status_code].__doc__.split("\n")[0],
            error_code=error_code,
            detail=detail,
            response=response_data,
        )

    if status_code >= 500:
        raise OpsManagerServerError(
            message=reason or "Server error",
            status_code=status_code,
            error_code=error_code,
            detail=detail,
            response=response_data,
        )

    # Generic error for unexpected status codes
    raise OpsManagerError(
        message=reason or f"HTTP {status_code}",
        status_code=status_code,
        error_code=error_code,
        detail=detail,
        response=response_data,
    )
