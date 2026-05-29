#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2026 Yurii Liubymyi <jurchello@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

# ----------------------------------------------------------------------------

"""HTTP client helpers for the GeneHelp integration API."""

import json
import mimetypes
import os
from urllib.parse import urlencode, urljoin
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from genehelp.api_contract import API_BASE_URL, PARTNER_API_USER_AGENT
from genehelp.models import SubmitPayload


class ApiError(RuntimeError):
    """API exception carrying the HTTP status, application code, and raw response payload.
    Callers use it to show concise user messages while keeping diagnostics available.
    """

    def __init__(
        self,
        message: str,
        status: int | None = None,
        code: str = "",
        payload: str = "",
        retry_after_seconds: int | None = None,
    ) -> None:
        """Initialize the object."""
        super().__init__(message)
        self.status = status
        self.code = code
        self.payload = payload
        self.retry_after_seconds = retry_after_seconds


class ApiClient:
    """Small HTTP client for GeneHelp integration endpoints.
    It owns URL building, authentication headers, JSON parsing, and multipart uploads.
    """

    def __init__(self, api_path: str, token: str, base_url: str = API_BASE_URL) -> None:
        """Initialize the object."""
        self.api_path = api_path
        self.token = token
        self.base_url = base_url.rstrip("/")

    def create_request(self, payload: SubmitPayload) -> dict:
        """Create request."""
        body, content_type = multipart_body(
            payload.fields,
            payload.file_field,
            payload.file_path,
        )
        request = Request(
            self.request_url(),
            data=body,
            headers=self.headers({"Content-Type": content_type}),
            method="POST",
        )
        return self._send_json_request(request)

    def get_countries(self, locale: str) -> dict:
        """Return countries."""
        return self.get_json({"locale": locale})

    def get_country_locales(self) -> dict:
        """Return country locales."""
        return self.get_json()

    def get_genealogy_requests(self, limit: int) -> dict:
        """Return genealogy requests."""
        return self.get_json({"limit": str(limit)})

    def get_help_offer(self) -> dict:
        """Return help offer."""
        return self.get_json()

    def get_json(self, query: dict[str, str] | None = None) -> dict:
        """Fetch JSON from the configured API endpoint."""
        request = Request(
            self.request_url(query),
            headers=self.headers(),
            method="GET",
        )
        return self._send_json_request(request)

    def headers(self, extra_headers: dict[str, str] | None = None) -> dict[str, str]:
        """Build API request headers."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "User-Agent": PARTNER_API_USER_AGENT,
            **(extra_headers or {}),
        }

    @staticmethod
    def _send_json_request(request: Request) -> dict:
        """Send json request."""
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            error_payload = exc.read().decode("utf-8", errors="replace")
            error_code, error_message = parse_api_error(error_payload)
            raise ApiError(
                f"HTTP {exc.code}: {error_message or error_payload}",
                status=exc.code,
                code=error_code,
                payload=error_payload,
                retry_after_seconds=parse_retry_after_seconds(exc.headers.get("Retry-After")),
            ) from exc
        except URLError as exc:
            raise ApiError(str(exc.reason)) from exc

    def request_url(self, query: dict[str, str] | None = None) -> str:
        """Request url."""
        url = self.base_url + self.api_path
        if query:
            url = f"{url}?{urlencode(query)}"
        return url

    def absolute_url(self, value: str) -> str:
        """Absolute url."""
        return absolute_url(value, self.base_url)


def parse_api_error(payload: str) -> tuple[str, str]:
    """Parse an API error payload."""
    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError:
        return "", ""

    error = decoded.get("error") if isinstance(decoded, dict) else None
    if isinstance(error, dict):
        code = error.get("code")
        message = error.get("message")
        return (
            code if isinstance(code, str) else "",
            message if isinstance(message, str) else "",
        )

    if not isinstance(decoded, dict):
        return "", ""

    message = decoded.get("message")
    return (
        "",
        message if isinstance(message, str) else "",
    )


def parse_retry_after_seconds(value: str | None) -> int | None:
    """Parse Retry-After delay seconds from an HTTP response header."""
    if value is None:
        return None

    try:
        seconds = int(value.strip())
    except ValueError:
        return None

    return seconds if seconds > 0 else None


def absolute_url(value: str, base_url: str = API_BASE_URL) -> str:
    """Absolute url."""
    if not value:
        return ""
    if value.startswith(("http://", "https://")):
        return value
    return urljoin(base_url.rstrip("/") + "/", value.lstrip("/"))


def multipart_body(fields: dict[str, str], file_field: str, file_path: str | None):
    """Multipart body."""
    boundary = f"----Genehelp{uuid4().hex}"
    chunks = []
    for key, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"))
        chunks.append(str(value).encode("utf-8"))
        chunks.append(b"\r\n")

    if file_path:
        filename = os.path.basename(file_path)
        mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(
            (
                f'Content-Disposition: form-data; name="{file_field}"; '
                f'filename="{filename}"\r\n'
            ).encode("utf-8")
        )
        chunks.append(f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"))
        with open(file_path, "rb") as media_file:
            chunks.append(media_file.read())
        chunks.append(b"\r\n")

    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))

    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"
