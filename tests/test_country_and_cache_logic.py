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

"""Unit tests for country parsing, cache handling, and country UI helpers."""

import json
import time
from typing import Any, cast

from genehelp import countries as countries_module
from genehelp.countries import (
    COUNTRIES_CACHE_SECONDS,
    CountryLocaleRepository,
    CountryRepository,
    cache_payload_is_fresh,
    normalize_language,
    parse_countries_response,
    parse_country_locales_response,
)
from genehelp.country_utils import (
    country_display,
    country_match_sort_key,
    country_matches_query,
    normalize_country_code,
)
from genehelp.models import CountryOption
from genehelp.ui_countries import CountryUiMixin


class FakeCountryApiClient:
    """API client test double for country repository tests."""

    calls: list[tuple[str, str]] = []

    def __init__(self, api_path: str, token: str, base_url: str = "") -> None:
        """Initialize the test double."""
        self.api_path = api_path
        self.token = token
        self.base_url = base_url

    def get_countries(self, locale: str) -> dict:
        """Return fake countries."""
        self.calls.append(("countries", locale))
        return {"data": [{"code": "UA", "name": "Ukraine"}]}

    def get_country_locales(self) -> dict:
        """Return fake country locales."""
        self.calls.append(("locales", self.token))
        return {"locales": ["uk", "en"], "fallback": "en"}


class FailingCountryApiClient(FakeCountryApiClient):
    """API client test double that simulates network failures."""

    def get_country_locales(self) -> dict:
        """Raise a fake country-locale loading failure."""
        raise RuntimeError("network down")


class DummyCountryUi(CountryUiMixin):
    """Country UI mixin host that avoids constructing GTK widgets."""

    UNKNOWN_COUNTRY_LABEL = "I do not know"
    COUNTRY_DROPDOWN_LIMIT = 4

    def __init__(self, countries: list[CountryOption]) -> None:
        """Initialize the test double."""
        self.all_countries = countries


def test_country_helpers_normalize_display_match_and_sort_queries() -> None:
    """Verify country helper functions normalize and rank values."""
    ukraine = CountryOption(code="UA", name="Ukraine")
    poland = CountryOption(code="PL", name="Poland")

    assert normalize_country_code(" ua ") == "UA"
    assert country_display(ukraine) == "UA - Ukraine"
    assert country_matches_query(ukraine, "ukr") is True
    assert country_matches_query(ukraine, "UA - ukr") is True
    assert country_matches_query(ukraine, "pol") is False
    assert country_match_sort_key(ukraine, "ua") < country_match_sort_key(poland, "ua")
    assert country_match_sort_key(poland, "poland")[0] == 1
    assert country_match_sort_key(poland, "po")[0] == 3


def test_country_response_ignores_invalid_records_and_keeps_duplicate_codes() -> None:
    """Verify country parsing filters invalid rows and preserves API duplicates."""
    countries = parse_countries_response(
        {
            "data": [
                {"code": "ua", "name": "Ukraine"},
                {"code": "UA", "name": "Ukraine duplicate"},
                {"code": "", "name": "Missing code"},
                {"code": "PL", "name": ""},
                "ignored",
            ]
        }
    )

    assert [(country.code, country.name) for country in countries] == [
        ("UA", "Ukraine"),
        ("UA", "Ukraine duplicate"),
    ]


def test_country_locale_parsing_handles_invalid_shapes_and_normalizes_languages() -> None:
    """Verify locale parsing handles invalid API shapes."""
    assert normalize_language(" uk-UA ") == "uk"
    assert normalize_language(None) == ""
    assert parse_country_locales_response({"locales": "uk", "fallback": 42}) == (
        [],
        "en",
    )
    assert parse_country_locales_response(
        {"locales": ["uk-UA", "uk", None, "EN_us"], "fallback": "PL-pl"}
    ) == (["uk", "en"], "pl")


def test_cache_payload_freshness_handles_missing_expired_and_future_timestamps() -> None:
    """Verify cache freshness calculation."""
    now = time.time()

    assert cache_payload_is_fresh({"fetched_at": now}, COUNTRIES_CACHE_SECONDS) is True
    assert cache_payload_is_fresh({"fetched_at": now + 60}, COUNTRIES_CACHE_SECONDS) is True
    assert cache_payload_is_fresh({"fetched_at": 0}, COUNTRIES_CACHE_SECONDS) is False
    assert cache_payload_is_fresh({}, COUNTRIES_CACHE_SECONDS) is False
    assert cache_payload_is_fresh(cast(dict[Any, Any], "invalid"), COUNTRIES_CACHE_SECONDS) is False


def test_country_locale_repository_returns_stale_cache_after_api_failure(
    monkeypatch,
    tmp_path,
) -> None:
    """Verify stale locale cache is used when API loading fails."""
    monkeypatch.setattr(countries_module, "USER_DATA_JSON_DIR", str(tmp_path))
    monkeypatch.setattr(countries_module, "ApiClient", FailingCountryApiClient)
    cache_path = tmp_path / "country_locales.json"
    cache_path.write_text(
        json.dumps(
            {
                "fetched_at": 0,
                "locales": ["uk", "en"],
                "fallback": "uk",
            }
        ),
        encoding="utf-8",
    )

    assert CountryLocaleRepository("token").locales() == (["uk", "en"], "uk")


def test_country_locale_repository_ignores_corrupted_cache(monkeypatch, tmp_path) -> None:
    """Verify corrupted locale cache does not break loading."""
    monkeypatch.setattr(countries_module, "USER_DATA_JSON_DIR", str(tmp_path))
    (tmp_path / "country_locales.json").write_text("{broken", encoding="utf-8")

    assert CountryLocaleRepository("token").load_cached(allow_stale=True) is None


def test_country_repository_uses_fresh_cache_before_api(monkeypatch, tmp_path) -> None:
    """Verify country repository prefers a fresh country cache."""
    monkeypatch.setattr(countries_module, "USER_DATA_JSON_DIR", str(tmp_path))
    monkeypatch.setattr(countries_module, "ApiClient", FakeCountryApiClient)
    FakeCountryApiClient.calls = []
    (tmp_path / "countries_en.json").write_text(
        json.dumps(
            {
                "fetched_at": int(time.time()),
                "data": [{"code": "PL", "name": "Poland"}],
            }
        ),
        encoding="utf-8",
    )

    countries = CountryRepository("token", locale="en-US").countries()

    assert countries == [CountryOption(code="PL", name="Poland")]
    assert not FakeCountryApiClient.calls


def test_country_repository_without_token_does_not_fetch(monkeypatch, tmp_path) -> None:
    """Verify country repository does not call API without a token."""
    monkeypatch.setattr(countries_module, "USER_DATA_JSON_DIR", str(tmp_path))
    monkeypatch.setattr(countries_module, "ApiClient", FakeCountryApiClient)
    FakeCountryApiClient.calls = []

    assert CountryRepository("", locale="en").countries() == []
    assert not FakeCountryApiClient.calls


def test_country_repository_saves_locale_specific_cache(monkeypatch, tmp_path) -> None:
    """Verify country repository saves country cache with locale-specific filename."""
    monkeypatch.setattr(countries_module, "USER_DATA_JSON_DIR", str(tmp_path))
    repository = CountryRepository("", locale="uk-UA")
    repository.save([CountryOption(code="UA", name="Ukraine")])

    payload = json.loads((tmp_path / "countries_uk.json").read_text(encoding="utf-8"))
    assert payload["locale"] == "uk"
    assert payload["data"] == [{"code": "UA", "name": "Ukraine"}]


def test_country_ui_visible_countries_keeps_selected_country_and_limits_results() -> None:
    """Verify visible countries keep selection and apply dropdown limit."""
    ui = DummyCountryUi(
        [
            CountryOption(code="UA", name="Ukraine"),
            CountryOption(code="PL", name="Poland"),
            CountryOption(code="DE", name="Germany"),
            CountryOption(code="US", name="United States"),
            CountryOption(code="CA", name="Canada"),
        ]
    )

    visible = ui.visible_countries("zz", "UA")

    assert visible == [CountryOption(code="UA", name="Ukraine")]
    assert ui.country_by_code(" pl ") == CountryOption(code="PL", name="Poland")
    assert ui.country_by_code("") is None
