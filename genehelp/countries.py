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

"""Country and locale loading with local cache support."""

import json
import os
import time

from gramps.gen.const import GRAMPS_LOCALE as glocale

from genehelp.api_client import ApiClient
from genehelp.api_contract import API_BASE_URL, COUNTRIES_PATH, COUNTRY_LOCALES_PATH
from genehelp.config import USER_DATA_JSON_DIR
from genehelp.diagnostics import print_exception_diagnostic
from genehelp.models import CountryOption

FALLBACK_COUNTRY_LOCALE = "en"
COUNTRY_LOCALES_CACHE_SECONDS = 7 * 24 * 60 * 60
COUNTRIES_CACHE_SECONDS = 30 * 24 * 60 * 60


class CountryRepository:
    """Repository for localized country options used by request forms.
    It prefers a fresh local cache and falls back to the GeneHelp API when needed.
    """

    def __init__(
        self,
        token: str,
        locale: str | None = None,
        base_url: str = API_BASE_URL,
    ) -> None:
        """Initialize the object."""
        self.token = token
        self.base_url = base_url
        self.requested_locale = normalize_language(locale or system_locale())
        self.locale = self.requested_locale or FALLBACK_COUNTRY_LOCALE
        cached_locales = CountryLocaleRepository(
            self.token,
            base_url=self.base_url,
        ).load_cached(allow_stale=True)
        if cached_locales is not None:
            locales, fallback = cached_locales
            self.locale = select_country_locale(
                self.requested_locale,
                locales,
                fallback,
            )

    def countries(self) -> list[CountryOption]:
        """Countries."""
        cached = self.load_cached()
        if cached:
            return cached

        if not self.token:
            return []

        self.resolve_locale()
        cached = self.load_cached()
        if cached:
            return cached

        countries = self.fetch()
        if countries:
            self.save(countries)
        return countries

    def resolve_locale(self) -> None:
        """Resolve locale."""
        locales, fallback = CountryLocaleRepository(self.token).locales()
        self.locale = select_country_locale(self.requested_locale, locales, fallback)

    def fetch(self) -> list[CountryOption]:
        """Fetch data from the GeneHelp API."""
        response = ApiClient(
            COUNTRIES_PATH,
            self.token,
            base_url=self.base_url,
        ).get_countries(self.locale)
        return parse_countries_response(response)

    def load_cached(self) -> list[CountryOption]:
        """Load cached data from disk."""
        path = self.cache_path()
        if not os.path.exists(path):
            return []

        try:
            with open(path, "r", encoding="utf-8") as countries_file:
                decoded = json.load(countries_file)
        except (OSError, json.JSONDecodeError):
            print_exception_diagnostic("GeneHelp countries cache cannot be read.")
            return []

        if not cache_payload_is_fresh(decoded, COUNTRIES_CACHE_SECONDS):
            return []

        return parse_countries_response(decoded)

    def save(self, countries: list[CountryOption]) -> None:
        """Save."""
        os.makedirs(USER_DATA_JSON_DIR, exist_ok=True)
        payload = {
            "fetched_at": int(time.time()),
            "locale": self.locale,
            "data": [
                {
                    "code": country.code,
                    "name": country.name,
                }
                for country in countries
            ],
        }

        try:
            with open(self.cache_path(), "w", encoding="utf-8") as countries_file:
                json.dump(payload, countries_file, ensure_ascii=False, indent=2)
        except OSError:
            print_exception_diagnostic("GeneHelp countries cache cannot be written.")

    def cache_path(self) -> str:
        """Cache path."""
        return os.path.join(USER_DATA_JSON_DIR, f"countries_{self.locale}.json")


class CountryLocaleRepository:
    """Repository for country-list locales supported by the GeneHelp API.
    It caches locale metadata separately so country loading can choose a stable locale.
    """

    def __init__(self, token: str, base_url: str = API_BASE_URL) -> None:
        """Initialize the object."""
        self.token = token
        self.base_url = base_url

    def locales(self) -> tuple[list[str], str]:
        """Locales."""
        cached = self.load_cached()
        if cached is not None:
            return cached

        if not self.token:
            return [], FALLBACK_COUNTRY_LOCALE

        try:
            locales, fallback = self.fetch()
            self.save(locales, fallback)
            return locales, fallback
        except Exception:  # pylint: disable=broad-except
            print_exception_diagnostic("GeneHelp country locales loading failed.")

        stale_cached = self.load_cached(allow_stale=True)
        if stale_cached is not None:
            return stale_cached

        return [], FALLBACK_COUNTRY_LOCALE

    def fetch(self) -> tuple[list[str], str]:
        """Fetch data from the GeneHelp API."""
        response = ApiClient(
            COUNTRY_LOCALES_PATH,
            self.token,
            base_url=self.base_url,
        ).get_country_locales()
        return parse_country_locales_response(response)

    def load_cached(self, allow_stale: bool = False) -> tuple[list[str], str] | None:
        """Load cached data from disk."""
        path = self.cache_path()
        if not os.path.exists(path):
            return None

        try:
            with open(path, "r", encoding="utf-8") as locales_file:
                decoded = json.load(locales_file)
        except (OSError, json.JSONDecodeError):
            print_exception_diagnostic("GeneHelp country locales cache cannot be read.")
            return None

        if not allow_stale and not cache_payload_is_fresh(
            decoded,
            COUNTRY_LOCALES_CACHE_SECONDS,
        ):
            return None

        return parse_country_locales_response(decoded)

    def save(self, locales: list[str], fallback: str) -> None:
        """Save."""
        os.makedirs(USER_DATA_JSON_DIR, exist_ok=True)
        payload = {
            "fetched_at": int(time.time()),
            "locales": locales,
            "fallback": fallback,
        }

        try:
            with open(self.cache_path(), "w", encoding="utf-8") as locales_file:
                json.dump(payload, locales_file, ensure_ascii=False, indent=2)
        except OSError:
            print_exception_diagnostic("GeneHelp country locales cache cannot be written.")

    @staticmethod
    def cache_path() -> str:
        """Cache path."""
        return os.path.join(USER_DATA_JSON_DIR, "country_locales.json")


def parse_country_locales_response(response: dict) -> tuple[list[str], str]:
    """Parse country locales response."""
    raw_locales = response.get("locales") if isinstance(response, dict) else None
    raw_fallback = response.get("fallback") if isinstance(response, dict) else None
    fallback = normalize_language(raw_fallback) or FALLBACK_COUNTRY_LOCALE

    locales = []
    if isinstance(raw_locales, list):
        for raw_locale in raw_locales:
            locale = normalize_language(raw_locale)
            if locale and locale not in locales:
                locales.append(locale)

    return locales, fallback


def select_country_locale(requested_locale: str, locales: list[str], fallback: str) -> str:
    """Select country locale."""
    if requested_locale in locales:
        return requested_locale
    return fallback or FALLBACK_COUNTRY_LOCALE


def cache_payload_is_fresh(payload: dict, ttl_seconds: int) -> bool:
    """Cache payload is fresh."""
    fetched_at = payload.get("fetched_at") if isinstance(payload, dict) else None
    if not isinstance(fetched_at, (int, float)):
        return False
    return time.time() - fetched_at <= ttl_seconds


def parse_countries_response(response: dict) -> list[CountryOption]:
    """Parse countries response."""
    data = response.get("data")
    if not isinstance(data, list):
        return []

    countries = []
    for item in data:
        if not isinstance(item, dict):
            continue

        code = item.get("code")
        name = item.get("name")
        if isinstance(code, str) and isinstance(name, str) and code and name:
            countries.append(CountryOption(code=code.upper(), name=name.strip()))

    return sorted(countries, key=lambda country: country.name.casefold())


def system_locale() -> str:
    """System locale."""
    language = glocale.language[0] if isinstance(glocale.language, list) else glocale.language
    return language or "en"


def normalize_language(locale) -> str:
    """Normalize language."""
    if not isinstance(locale, str):
        return ""
    return locale.replace("-", "_").split("_", 1)[0].strip().lower()
