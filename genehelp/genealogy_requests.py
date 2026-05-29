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

"""GeneHelp genealogy request list API parsing and loading."""

from genehelp.api_client import ApiClient, absolute_url
from genehelp.api_contract import API_BASE_URL, GENEALOGY_REQUESTS_PATH
from genehelp.models import GenealogyRequestGroup, GenealogyRequestItem


class GenealogyRequestRepository:
    """Repository for the owner genealogy request list shown in the gramplet.
    It normalizes relative API URLs before handing items to the UI layer.
    """

    def __init__(self, token: str, base_url: str = API_BASE_URL) -> None:
        """Initialize the object."""
        self.client = ApiClient(GENEALOGY_REQUESTS_PATH, token, base_url=base_url)

    def fetch(self, limit: int = 100) -> list[GenealogyRequestGroup]:
        """Fetch data from the GeneHelp API."""
        response = self.client.get_genealogy_requests(limit)
        return parse_genealogy_requests_response(response, base_url=self.client.base_url)


def parse_genealogy_requests_response(
    response: dict,
    base_url: str = API_BASE_URL,
) -> list[GenealogyRequestGroup]:
    """Parse genealogy requests response."""
    data = response.get("data") if isinstance(response, dict) else None
    if not isinstance(data, list):
        return []

    groups = []
    for raw_group in data:
        if not isinstance(raw_group, dict):
            continue

        items = tuple(parse_genealogy_request_items(raw_group.get("items"), base_url))
        groups.append(
            GenealogyRequestGroup(
                helper_country_code=string_or_empty(raw_group.get("helper_country_code")),
                count=int_or_default(raw_group.get("count"), len(items)),
                items=items,
            )
        )
    return groups


def parse_genealogy_request_items(
    raw_items,
    base_url: str = API_BASE_URL,
) -> list[GenealogyRequestItem]:
    """Parse genealogy request items."""
    if not isinstance(raw_items, list):
        return []

    items = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue

        item_id = string_or_empty(raw_item.get("id"))
        title = string_or_empty(raw_item.get("title"))
        url = absolute_url(string_or_empty(raw_item.get("url")), base_url)
        if not item_id or not title or not url:
            continue

        interaction_url = absolute_url(
            string_or_empty(raw_item.get("interaction_url")),
            base_url,
        )
        edit_url = absolute_url(string_or_empty(raw_item.get("edit_url")), base_url)
        items.append(
            GenealogyRequestItem(
                id=item_id,
                title=title,
                url=url,
                edit_url=edit_url,
                status=string_or_empty(raw_item.get("status")),
                is_test=bool_or_default(raw_item.get("is_test")),
                created_at=string_or_empty(raw_item.get("created_at")),
                interaction_url=interaction_url,
            )
        )
    return items


def string_or_empty(value) -> str:
    """String or empty."""
    return value if isinstance(value, str) else ""


def int_or_default(value, default: int) -> int:
    """Int or default."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def bool_or_default(value) -> bool:
    """Bool or default."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    if isinstance(value, int):
        return value == 1
    return False
