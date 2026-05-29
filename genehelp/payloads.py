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

"""Utilities for building GeneHelp request payloads from Gramps objects."""

from genehelp.api_contract import (
    COUNTRY_SOURCE_UNKNOWN,
    COUNTRY_SOURCE_USER_SELECTED,
    FIELD_DESCRIPTION,
    FIELD_HELPER_COUNTRY_CODE,
    FIELD_HELPER_COUNTRY_SOURCE,
    FIELD_IS_TEST,
    FIELD_MEDIA,
    FIELD_REQUEST_COUNTRY_CODE,
    FIELD_REQUEST_COUNTRY_SOURCE,
    FIELD_THEME,
    FIELD_TITLE,
)
from genehelp.models import ImportedContext, SubmitPayload, ThemeOption


def build_submit_payload(
    imported_context: ImportedContext,
    theme: ThemeOption,
    title: str,
    description: str,
    request_country_code: str,
    helper_country_code: str,
    is_test: bool = False,
) -> SubmitPayload:
    """Build submit payload."""
    title = title.strip()
    description = description.strip()
    request_country_code = request_country_code.strip().upper()
    helper_country_code = helper_country_code.strip().upper()
    if not title or not description:
        raise ValueError("Missing submit payload fields.")

    return SubmitPayload(
        fields={
            FIELD_THEME: theme.api_theme,
            FIELD_TITLE: title,
            FIELD_DESCRIPTION: description,
            FIELD_REQUEST_COUNTRY_CODE: request_country_code,
            FIELD_REQUEST_COUNTRY_SOURCE: country_source(request_country_code),
            FIELD_HELPER_COUNTRY_CODE: helper_country_code,
            FIELD_HELPER_COUNTRY_SOURCE: country_source(helper_country_code),
            FIELD_IS_TEST: "1" if is_test else "0",
        },
        file_field=FIELD_MEDIA,
        file_path=imported_context.file_path,
    )


def country_source(country_code: str) -> str:
    """Country source."""
    return COUNTRY_SOURCE_USER_SELECTED if country_code else COUNTRY_SOURCE_UNKNOWN
