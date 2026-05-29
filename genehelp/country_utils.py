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

"""Country normalization, display, and search helpers."""

from genehelp.l10n import _
from genehelp.models import CountryOption

UNKNOWN_COUNTRY_LABEL = _("I do not know")
COUNTRY_DROPDOWN_LIMIT = 10


def country_display(country: CountryOption) -> str:
    """Country display."""
    return f"{country.code} - {country.name}"


def country_sort_key(country: CountryOption):
    """Country sort key."""
    return country.name.casefold(), country.code


def normalize_country_code(country_code: str) -> str:
    """Normalize country code."""
    return (country_code or "").strip().upper()


def country_matches_query(country: CountryOption, query: str) -> bool:
    """Country matches query."""
    normalized_query = query.casefold()
    return (
        normalized_query in country.code.casefold()
        or normalized_query in country.name.casefold()
        or normalized_query in country_display(country).casefold()
    )


def country_match_sort_key(country: CountryOption, query: str):
    """Country match sort key."""
    normalized_query = query.casefold()
    code = country.code.casefold()
    name = country.name.casefold()
    display = country_display(country).casefold()

    if not normalized_query:
        return 0, country.name.casefold(), country.code
    if code == normalized_query:
        rank = 0
    elif name == normalized_query:
        rank = 1
    elif code.startswith(normalized_query):
        rank = 2
    elif name.startswith(normalized_query):
        rank = 3
    elif display.startswith(normalized_query):
        rank = 4
    else:
        rank = 5

    return rank, country.name.casefold(), country.code


def country_completion_match(completion, key: str, tree_iter, *_user_data) -> bool:
    """Country completion match."""
    model = completion.get_model()
    key_casefold = key.casefold()
    code = model[tree_iter][0].casefold()
    name = model[tree_iter][1].casefold()
    display = model[tree_iter][2].casefold()
    return key_casefold in code or key_casefold in name or key_casefold in display
