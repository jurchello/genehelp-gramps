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

"""Configuration keys, defaults, and Gramps data paths for the gramplet."""

import os

from gramps.gen.const import USER_DATA
from gramps.gen.config import config as configman

from genehelp.api_contract import DEFAULT_API_BASE_URL, GENEALOGY_REQUESTS_PATH
from genehelp.country_utils import normalize_country_code
from genehelp.l10n import _

MAX_MEDIA_BYTES = 3 * 1024 * 1024
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
INTEGRATION_GENEALOGY_REQUESTS_PATH = GENEALOGY_REQUESTS_PATH

DATA_SOURCE_MEDIA = "Media"
DATA_SOURCE_NOTE = "Note"
DATA_SOURCE_REPOSITORY = "Repository"
DATA_SOURCE_CITATION = "Citation"
DATA_SOURCE_SOURCE = "Source"
DATA_SOURCE_PLACE = "Place"
DATA_SOURCE_EVENT = "Event"
DATA_SOURCE_FAMILY = "Family"
DATA_SOURCE_PERSON = "Person"

API_TOKEN_OPTION_LABEL = _("Integration token")
DEFAULT_REQUEST_COUNTRY_OPTION_LABEL = _("Request author's country")
API_URL_CONFIG_KEY = "genehelp.api_url"

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.dirname(PACKAGE_DIR)
UI_FILE = os.path.join(PLUGIN_DIR, "Genehelp.xml")
CSS_FILE = os.path.join(PLUGIN_DIR, "Genehelp.css")
USER_DATA_BASE_DIR = os.path.join(USER_DATA, "Genehelp")
USER_DATA_JSON_DIR = os.path.join(USER_DATA_BASE_DIR, "json")


class Config:
    """Persistent Gramps configuration wrapper for the gramplet.
    It stores the integration token and the default request author country code.
    """

    def __init__(self) -> None:
        """Initialize the object."""
        self.config = configman.register_manager("genehelp")
        self.config.register("genehelp.api_token", "")
        self.config.register(API_URL_CONFIG_KEY, "")
        self.config.register("genehelp.default_request_country_code", "")
        self.config.load()

    def api_token(self) -> str:
        """Api token."""
        return (self.config.get("genehelp.api_token") or "").strip()

    def api_base_url(self) -> str:
        """Return configured API base URL or production default."""
        return normalize_api_base_url(self.config.get(API_URL_CONFIG_KEY) or "")

    def default_request_country_code(self) -> str:
        """Default request country code."""
        return normalize_country_code(
            self.config.get("genehelp.default_request_country_code") or ""
        )

    def save(
        self,
        api_token: str,
        default_request_country_code: str,
    ) -> None:
        """Save."""
        self.config.set("genehelp.api_token", (api_token or "").strip())
        self.config.set(
            "genehelp.default_request_country_code",
            normalize_country_code(default_request_country_code),
        )
        self.config.save()


def normalize_api_base_url(value: str) -> str:
    """Normalize API base URL config value."""
    normalized = (value or "").strip().strip("'\"").rstrip("/")
    if not normalized:
        return DEFAULT_API_BASE_URL
    if normalized.startswith(("http://", "https://")):
        return normalized
    return DEFAULT_API_BASE_URL
