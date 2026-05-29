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

"""Unit tests for GeneHelp gramplet controller logic."""

from typing import Any

import Genehelp as controller_module
from Genehelp import (
    GeneHelpGramplet,
    api_error_message_for_exception,
    edit_url_from_public_url,
    retry_after_minutes_from_seconds,
)
from genehelp.api_client import ApiError
from genehelp.api_contract import (
    FIELD_DESCRIPTION,
    FIELD_HELPER_COUNTRY_CODE,
    FIELD_IS_TEST,
    FIELD_REQUEST_COUNTRY_CODE,
    FIELD_THEME,
    FIELD_TITLE,
    API_BASE_URL,
)
from genehelp.config import DATA_SOURCE_MEDIA, DATA_SOURCE_PERSON
from genehelp.models import ImportedContext


class FakeOption:
    """Minimal Gramps option test double."""

    def __init__(self, value: str) -> None:
        """Initialize the test double."""
        self.value = value

    def get_value(self) -> str:
        """Return the stored value."""
        return self.value


class FakeSubmitUi:
    """Minimal UI test double for submit-state and submit-flow tests."""

    def __init__(
        self,
        title: str = "Title",
        description: str = "Description",
        theme_key: str = "identify_photo",
        request_country_code: str = "UA",
        helper_country_code: str = "PL",
        is_test: bool = False,
    ) -> None:
        """Initialize the test double."""
        self.title = title
        self.description = description
        self.theme_key = theme_key
        self.request_country = request_country_code
        self.helper_country = helper_country_code
        self.is_test = is_test
        self.submit_sensitive_values: list[bool] = []
        self.reset_nav_types: list[str | None] = []

    def title_text(self) -> str:
        """Return request title text."""
        return self.title

    def description_text(self) -> str:
        """Return request description text."""
        return self.description

    def selected_theme_key(self, _nav_type: str) -> str:
        """Return selected request topic key."""
        return self.theme_key

    def request_country_code(self) -> str:
        """Return request country code."""
        return self.request_country

    def helper_country_code(self) -> str:
        """Return helper country code."""
        return self.helper_country

    def is_test_request(self) -> bool:
        """Return whether the request is marked as a test request."""
        return self.is_test

    def set_submit_sensitive(self, value: bool) -> None:
        """Record submit button state."""
        self.submit_sensitive_values.append(value)

    def reset_imported_payload(self, nav_type: str | None) -> None:
        """Record form reset calls."""
        self.reset_nav_types.append(nav_type)


class FakeRefreshUi:
    """Minimal UI test double for refresh flows."""

    def __init__(self) -> None:
        """Initialize the test double."""
        self.request_refresh_visibility: list[bool] = []
        self.help_offer_refresh_visibility: list[bool] = []
        self.request_errors = 0
        self.help_offer_errors = 0

    def set_requests_refresh_visible(self, visible: bool) -> None:
        """Record request refresh visibility."""
        self.request_refresh_visibility.append(visible)

    def show_genealogy_requests_error(self) -> None:
        """Record request list error rendering."""
        self.set_requests_refresh_visible(False)
        self.request_errors += 1

    def set_genealogy_requests(self, _groups) -> None:
        """Accept rendered request groups."""

    def set_help_offer_refresh_visible(self, visible: bool) -> None:
        """Record help profile refresh visibility."""
        self.help_offer_refresh_visibility.append(visible)

    def show_help_offer_error(self) -> None:
        """Record help profile error rendering."""
        self.set_help_offer_refresh_visible(False)
        self.help_offer_errors += 1

    def set_help_offer(self, _offer) -> None:
        """Accept rendered help profile."""


def gramplet_for_submit(ui: FakeSubmitUi, token: str = "token") -> Any:
    """Build a controller instance without running Gramps or GTK initialization."""
    gramplet: Any = object.__new__(GeneHelpGramplet)
    gramplet.current_nav_type = DATA_SOURCE_MEDIA
    gramplet.imported_context = ImportedContext(
        nav_type=DATA_SOURCE_MEDIA,
        handle="media-1",
        description="Imported",
        file_path="/tmp/photo.jpg",
    )
    gramplet.ui = ui
    gramplet.api_token_option = FakeOption(token)
    gramplet.default_request_country_widget = None
    gramplet.default_request_country_option = FakeOption("")
    gramplet.api_base_url = API_BASE_URL
    gramplet.requests_loaded = True
    gramplet.save_options = lambda: None
    gramplet.show_notification = lambda *_args, **_kwargs: None
    return gramplet


def gramplet_for_refresh(ui: FakeRefreshUi, token: str = "token") -> Any:
    """Build a controller instance for refresh tests."""
    gramplet: Any = object.__new__(GeneHelpGramplet)
    gramplet.ui = ui
    gramplet.api_token_option = FakeOption(token)
    gramplet.default_request_country_widget = None
    gramplet.default_request_country_option = FakeOption("")
    gramplet.api_base_url = API_BASE_URL
    gramplet.requests_loaded = True
    gramplet.requests_fetching = False
    gramplet.help_offer_loaded = True
    gramplet.help_offer_fetching = False
    gramplet.load_cached_countries = lambda: None
    gramplet.load_countries = lambda: None
    return gramplet


def test_can_submit_requires_context_matching_form_theme_and_token() -> None:
    """Verify submit gating requires all form prerequisites."""
    ui = FakeSubmitUi()
    gramplet = gramplet_for_submit(ui)

    assert gramplet.can_submit() is True

    gramplet.imported_context = None
    assert gramplet.can_submit() is False

    gramplet.imported_context = ImportedContext(
        nav_type=DATA_SOURCE_PERSON,
        handle="person-1",
        description="Imported",
    )
    assert gramplet.can_submit() is False

    gramplet.imported_context = ImportedContext(
        nav_type=DATA_SOURCE_MEDIA,
        handle="media-1",
        description="Imported",
    )
    ui.title = " "
    assert gramplet.can_submit() is False

    ui.title = "Title"
    ui.description = " "
    assert gramplet.can_submit() is False

    ui.description = "Description"
    ui.theme_key = ""
    assert gramplet.can_submit() is False

    ui.theme_key = "identify_photo"
    gramplet.api_token_option = FakeOption("")
    assert gramplet.can_submit() is False


def test_selected_theme_uses_imported_context_nav_type() -> None:
    """Verify selected theme comes from the imported context navigation type."""
    ui = FakeSubmitUi(theme_key="person_find_birth_record")
    gramplet = gramplet_for_submit(ui)
    gramplet.imported_context = ImportedContext(
        nav_type=DATA_SOURCE_PERSON,
        handle="person-1",
        description="Imported",
    )

    theme = gramplet.selected_theme()

    assert theme is not None
    assert theme.key == "person_find_birth_record"


def test_on_submit_builds_payload_with_test_flag_and_countries(monkeypatch) -> None:
    """Verify submit sends the expected payload into the integration API client."""
    created_payloads: list[tuple[str, str, Any]] = []
    opened_responses: list[dict[str, str]] = []

    class FakeApiClient:
        """API client test double that records created payloads."""

        def __init__(self, api_path: str, token: str, base_url: str = API_BASE_URL) -> None:
            """Initialize the test double."""
            self.api_path = api_path
            self.token = token
            self.base_url = base_url

        def create_request(self, payload):
            """Record create request payload."""
            created_payloads.append((self.api_path, self.token, payload))
            return {"edit_url": "/requests/1/edit"}

    monkeypatch.setattr(controller_module, "ApiClient", FakeApiClient)
    ui = FakeSubmitUi(is_test=True)
    gramplet = gramplet_for_submit(ui, token="secret-token")
    gramplet.open_created_request = opened_responses.append

    gramplet.on_submit(None)

    assert len(created_payloads) == 1
    api_path, token, payload = created_payloads[0]
    assert api_path == controller_module.INTEGRATION_GENEALOGY_REQUESTS_PATH
    assert token == "secret-token"
    assert payload.fields[FIELD_THEME] == "identify_photo"
    assert payload.fields[FIELD_TITLE] == "Title"
    assert payload.fields[FIELD_DESCRIPTION] == "Description"
    assert payload.fields[FIELD_REQUEST_COUNTRY_CODE] == "UA"
    assert payload.fields[FIELD_HELPER_COUNTRY_CODE] == "PL"
    assert payload.fields[FIELD_IS_TEST] == "1"
    assert payload.file_path == "/tmp/photo.jpg"
    assert gramplet.requests_loaded is False
    assert gramplet.imported_context is None
    assert ui.reset_nav_types == [DATA_SOURCE_MEDIA]
    assert opened_responses == [{"edit_url": "/requests/1/edit"}]


def test_open_created_request_prefers_edit_url(monkeypatch) -> None:
    """Verify created request opening prefers edit_url over public url."""
    opened_urls: list[str] = []
    gramplet: Any = object.__new__(GeneHelpGramplet)
    gramplet.api_token_option = FakeOption("token")
    gramplet.default_request_country_widget = None
    gramplet.default_request_country_option = FakeOption("")
    gramplet.api_base_url = API_BASE_URL
    monkeypatch.setattr(controller_module.webbrowser, "open", opened_urls.append)

    gramplet.open_created_request(
        {
            "edit_url": "/requests/1/edit",
            "url": "/requests/1",
        }
    )

    assert opened_urls == [f"{API_BASE_URL}/requests/1/edit"]


def test_open_created_request_falls_back_to_public_url_edit_route(monkeypatch) -> None:
    """Verify created request opening derives edit route from a public URL."""
    opened_urls: list[str] = []
    gramplet: Any = object.__new__(GeneHelpGramplet)
    gramplet.api_token_option = FakeOption("token")
    gramplet.default_request_country_widget = None
    gramplet.default_request_country_option = FakeOption("")
    gramplet.api_base_url = API_BASE_URL
    monkeypatch.setattr(controller_module.webbrowser, "open", opened_urls.append)

    gramplet.open_created_request({"url": "/requests/1"})

    assert opened_urls == [f"{API_BASE_URL}/requests/1/edit"]


def test_edit_url_from_public_url_normalizes_empty_existing_and_plain_urls() -> None:
    """Verify edit URL fallback normalizes supported public URL shapes."""
    assert edit_url_from_public_url("") == ""
    assert edit_url_from_public_url("  /requests/1/  ") == "/requests/1/edit"
    assert edit_url_from_public_url("/requests/1/edit") == "/requests/1/edit"


def test_user_message_for_exception_includes_status_detail_or_network_reason() -> None:
    """Verify user-facing exception message includes status detail or network reason."""

    class FakeStatusError(Exception):
        """Exception test double carrying an HTTP status."""

        status = 422

    status_message = GeneHelpGramplet.user_message_for_exception(
        FakeStatusError("HTTP 422: Title is required.")
    )

    assert "HTTP status: 422" in status_message
    assert "Title is required" in status_message
    assert "Reason: Connection refused" in GeneHelpGramplet.user_message_for_exception(
        RuntimeError("Connection refused")
    )
    assert "HTTP status: missing" in GeneHelpGramplet.user_message_for_exception(RuntimeError())


def test_user_message_for_exception_uses_known_api_error_codes() -> None:
    """Verify user-facing API errors are mapped by backend code."""
    token_message = GeneHelpGramplet.user_message_for_exception(
        ApiError("HTTP 401: backend text", status=401, code="integration_token_invalid")
    )
    validation_message = GeneHelpGramplet.user_message_for_exception(
        ApiError("HTTP 422: backend text", status=422, code="validation_failed")
    )

    assert "invalid or revoked" in token_message
    assert "Please try again" not in token_message
    assert "backend text" not in token_message
    assert "Check the title, description, countries, and media file" in validation_message


def test_user_message_for_exception_rounds_retry_after_seconds_up_to_minutes() -> None:
    """Verify rate limit retry seconds are displayed as rounded-up minutes."""
    message = GeneHelpGramplet.user_message_for_exception(
        ApiError(
            "HTTP 429: backend text",
            status=429,
            code="too_many_requests",
            retry_after_seconds=61,
        )
    )

    assert "Wait 2 minute(s) and try again" in message
    assert "61" not in message


def test_api_error_message_for_exception_reuses_rate_limit_message() -> None:
    """Verify API exception mapping is shared outside the create-request flow."""
    message = api_error_message_for_exception(
        ApiError(
            "HTTP 429: backend text",
            status=429,
            code="too_many_requests",
            retry_after_seconds=61,
        )
    )

    assert message == "Too many requests were sent. Wait 2 minute(s) and try again."


def test_refresh_genealogy_requests_shows_localized_api_error(monkeypatch) -> None:
    """Verify manual request-list refresh can show API error notifications."""
    notifications: list[tuple[str, str]] = []

    class FailingRepository:
        """Repository test double that raises a rate limit error."""

        def __init__(self, _token: str, base_url: str = API_BASE_URL) -> None:
            """Initialize the test double."""
            self.base_url = base_url

        def fetch(self):
            """Raise a rate limit error."""
            raise ApiError(
                "HTTP 429: backend text",
                status=429,
                code="too_many_requests",
                retry_after_seconds=61,
            )

    monkeypatch.setattr(controller_module, "GenealogyRequestRepository", FailingRepository)
    ui = FakeRefreshUi()
    gramplet = gramplet_for_refresh(ui)
    gramplet.show_notification = lambda message, kind="success": notifications.append(
        (message, kind)
    )

    gramplet.refresh_genealogy_requests()

    assert gramplet.requests_loaded is False
    assert ui.request_refresh_visibility == [False, False]
    assert ui.request_errors == 1
    assert notifications == [
        ("Too many requests were sent. Wait 2 minute(s) and try again.", "error")
    ]


def test_refresh_help_offer_shows_localized_api_error(monkeypatch) -> None:
    """Verify manual help-profile refresh can show API error notifications."""
    notifications: list[tuple[str, str]] = []

    class FailingRepository:
        """Repository test double that raises a rate limit error."""

        def __init__(self, _token: str, base_url: str = API_BASE_URL) -> None:
            """Initialize the test double."""
            self.base_url = base_url

        def fetch(self):
            """Raise a rate limit error."""
            raise ApiError(
                "HTTP 429: backend text",
                status=429,
                code="too_many_requests",
                retry_after_seconds=61,
            )

    monkeypatch.setattr(controller_module, "HelpOfferRepository", FailingRepository)
    ui = FakeRefreshUi()
    gramplet = gramplet_for_refresh(ui)
    gramplet.show_notification = lambda message, kind="success": notifications.append(
        (message, kind)
    )

    gramplet.refresh_help_offer()

    assert gramplet.help_offer_loaded is False
    assert ui.help_offer_refresh_visibility == [False, False]
    assert ui.help_offer_errors == 1
    assert notifications == [
        ("Too many requests were sent. Wait 2 minute(s) and try again.", "error")
    ]


def test_retry_after_minutes_from_seconds_rounds_up_without_hours() -> None:
    """Verify retry-after seconds convert to rounded-up minute count."""
    assert retry_after_minutes_from_seconds(None) is None
    assert retry_after_minutes_from_seconds(0) is None
    assert retry_after_minutes_from_seconds(1) == 1
    assert retry_after_minutes_from_seconds(60) == 1
    assert retry_after_minutes_from_seconds(61) == 2
    assert retry_after_minutes_from_seconds(3601) == 61
