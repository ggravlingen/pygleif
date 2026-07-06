"""Errors for the pygleif v2 client."""

from __future__ import annotations


class PyGLEIFError(Exception):
    """Base error for v2."""


class PyGLEIFApiError(PyGLEIFError):
    """Raised for HTTP / transport failures against the GLEIF API.

    Carries the request context when available: ``status_code`` (``None``
    for network-level failures), the requested ``url``, and a ``body``
    excerpt of the error response.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        url: str | None = None,
        body: str | None = None,
    ) -> None:
        """Init the error with its message and request context."""
        super().__init__(message)
        self.status_code = status_code
        self.url = url
        self.body = body


class PyGLEIFNotFoundError(PyGLEIFApiError):
    """Raised when a requested resource does not exist (HTTP 404)."""


class PyGLEIFRateLimitError(PyGLEIFApiError):
    """Raised when the GLEIF rate limit is exceeded (HTTP 429).

    ``retry_after`` holds the server-suggested wait in seconds, when the
    response carried a ``Retry-After`` header in integer-seconds form.
    """

    def __init__(
        self,
        message: str,
        *,
        retry_after: float | None = None,
        status_code: int | None = None,
        url: str | None = None,
        body: str | None = None,
    ) -> None:
        """Init the error with the server-suggested retry delay."""
        super().__init__(message, status_code=status_code, url=url, body=body)
        self.retry_after = retry_after
