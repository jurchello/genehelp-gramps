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

"""Shared API paths, field names, and integration constants."""

COUNTRIES_PATH = "/api/partners/countries"
COUNTRY_LOCALES_PATH = "/api/partners/countries/locales"
HELP_OFFER_PATH = "/api/partners/help-offer"
DEFAULT_API_BASE_URL = "https://genehelp.online"
API_BASE_URL = DEFAULT_API_BASE_URL

GENEALOGY_REQUESTS_PATH = "/api/partners/genealogy-requests"

COUNTRIES_THROTTLE = "5 requests per 1 minute"
HELP_OFFER_THROTTLE = "10 requests per 1 minute"
GENEALOGY_REQUESTS_THROTTLE = "2 requests per 1 minute"
GENEALOGY_REQUEST_LIST_THROTTLE = "10 requests per 1 minute"

PARTNER_API_USER_AGENT = "GeneHelp-Gramps/1.0"

FIELD_THEME = "theme"
FIELD_TITLE = "title"
FIELD_DESCRIPTION = "description"
FIELD_MEDIA = "media"
FIELD_REQUEST_COUNTRY_CODE = "request_country_code"
FIELD_REQUEST_COUNTRY_SOURCE = "request_country_source"
FIELD_HELPER_COUNTRY_CODE = "helper_country_code"
FIELD_HELPER_COUNTRY_SOURCE = "helper_country_source"
FIELD_IS_TEST = "is_test"

COUNTRY_SOURCE_UNKNOWN = "unknown"
COUNTRY_SOURCE_INFERRED = "inferred"
COUNTRY_SOURCE_USER_SELECTED = "user_selected"
