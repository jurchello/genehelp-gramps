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

"""GeneHelp help profile API parsing and loading."""

from typing import Any

from genehelp.api_client import ApiClient, absolute_url
from genehelp.api_contract import API_BASE_URL, HELP_OFFER_PATH
from genehelp.models import (
    HelpOffer,
    HelpOfferAccessPoint,
    HelpOfferDocumentType,
    HelpOfferEnabledValue,
    HelpOfferHistoricalPeriod,
    HelpOfferSection,
)


class HelpOfferRepository:
    """Repository for the owner help profile shown in the gramplet.
    It converts API response sections into typed objects for the GTK renderer.
    """

    def __init__(self, token: str, base_url: str = API_BASE_URL) -> None:
        """Initialize the object."""
        self.client = ApiClient(HELP_OFFER_PATH, token, base_url=base_url)

    def fetch(self) -> HelpOffer | None:
        """Fetch data from the GeneHelp API."""
        response = self.client.get_help_offer()
        return parse_help_offer_response(response, base_url=self.client.base_url)


def parse_help_offer_response(response: dict, base_url: str = API_BASE_URL) -> HelpOffer | None:
    """Parse help offer response."""
    data = response.get("data") if isinstance(response, dict) else None
    if not isinstance(data, dict):
        return None

    channels = tuple(parse_channels(data))
    conditions = parse_conditions(data.get("conditions"))
    capabilities = tuple(parse_enabled_values(data.get("capabilities")))
    historical_periods = tuple(parse_historical_periods(data.get("historical_periods")))
    document_types = tuple(parse_document_types(data.get("document_types")))
    access_points = tuple(parse_access_points(data.get("access_points")))
    sections = tuple(parse_sections(data.get("sections")))

    return HelpOffer(
        user_id=string_or_empty(data.get("user_id")),
        profile_url=absolute_url(string_or_empty(data.get("profile_url")), base_url),
        can_online=bool(data.get("can_online")),
        can_offline=bool(data.get("can_offline")),
        helper_country_code=string_or_empty(data.get("helper_country_code")),
        helper_country_source=string_or_empty(data.get("helper_country_source")),
        channels=channels,
        conditions=conditions,
        capabilities=capabilities,
        historical_periods=historical_periods,
        document_types=document_types,
        access_points=access_points,
        sections=sections,
    )


def parse_enabled_values(raw_items: Any) -> list[HelpOfferEnabledValue]:
    """Parse enabled values."""
    if not isinstance(raw_items, list):
        return []

    values = []
    for raw_item in raw_items:
        if isinstance(raw_item, str):
            values.append(HelpOfferEnabledValue(key=raw_item, label=raw_item, enabled=True))
            continue
        if not isinstance(raw_item, dict):
            continue

        key = string_or_empty(raw_item.get("key"))
        if key:
            values.append(
                HelpOfferEnabledValue(
                    key=key,
                    label=string_or_empty(raw_item.get("label")),
                    description=string_or_empty(raw_item.get("description")),
                    enabled=bool(raw_item.get("enabled")),
                )
            )
    return values


def parse_conditions(raw_conditions: Any) -> tuple[HelpOfferEnabledValue, ...]:
    """Parse conditions."""
    if isinstance(raw_conditions, list):
        return tuple(parse_enabled_values(raw_conditions))
    return ()


def parse_historical_periods(raw_items: Any) -> list[HelpOfferHistoricalPeriod]:
    """Parse historical periods."""
    if not isinstance(raw_items, list):
        return []

    periods = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        periods.append(
            HelpOfferHistoricalPeriod(
                key=string_or_empty(raw_item.get("key")),
                selection_type=string_or_empty(raw_item.get("selection_type")),
                selection_type_label=string_or_empty(raw_item.get("selection_type_label")),
                label=string_or_empty(raw_item.get("label")),
                enabled=bool(raw_item.get("enabled", True)),
                range_key=string_or_empty(raw_item.get("range_key")),
                context_key=string_or_empty(raw_item.get("context_key")),
                from_year=optional_int(raw_item.get("from_year")),
                to_year=optional_int(raw_item.get("to_year")),
            )
        )
    return periods


def parse_document_types(raw_items: Any) -> list[HelpOfferDocumentType]:
    """Parse document types."""
    if not isinstance(raw_items, list):
        return []

    document_types = []
    for raw_item in raw_items:
        if isinstance(raw_item, str):
            document_types.append(HelpOfferDocumentType(key=raw_item, label=raw_item))
            continue
        if not isinstance(raw_item, dict):
            continue
        key = string_or_empty(raw_item.get("key")) or string_or_empty(
            raw_item.get("document_type_key")
        )
        if key:
            document_types.append(
                HelpOfferDocumentType(
                    key=key,
                    label=string_or_empty(raw_item.get("label")),
                    enabled=bool(raw_item.get("enabled", True)),
                )
            )
    return document_types


def parse_access_points(raw_items: Any) -> list[HelpOfferAccessPoint]:
    """Parse access points."""
    if not isinstance(raw_items, list):
        return []

    access_points = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        access_points.append(
            HelpOfferAccessPoint(
                location_type=string_or_empty(raw_item.get("location_type")),
                location_type_label=string_or_empty(raw_item.get("location_type_label")),
                country_code=string_or_empty(raw_item.get("country_code")),
                place_name=string_or_empty(raw_item.get("place_name")),
                region=string_or_empty(raw_item.get("region")),
                district=string_or_empty(raw_item.get("district")),
                region_wide=bool(raw_item.get("region_wide")),
                administrative_area_name=string_or_empty(raw_item.get("administrative_area_name")),
                object_type_label=string_or_empty(raw_item.get("object_type_label")),
                object_name=string_or_empty(raw_item.get("object_name")),
                radius_km=optional_int(raw_item.get("radius_km")),
                purpose=string_or_empty(raw_item.get("purpose")),
            )
        )
    return access_points


def parse_sections(raw_sections: Any) -> list[HelpOfferSection]:
    """Parse sections."""
    if not isinstance(raw_sections, list):
        return []

    sections = []
    for raw_section in raw_sections:
        if not isinstance(raw_section, dict):
            continue

        key = string_or_empty(raw_section.get("key"))
        section_type = string_or_empty(raw_section.get("type"))
        items = parse_section_items(key, section_type, raw_section.get("items"))
        sections.append(
            HelpOfferSection(
                key=key,
                label=string_or_empty(raw_section.get("label")),
                type=section_type,
                items=tuple(items),
            )
        )

    return sections


def parse_section_items(key: str, section_type: str, raw_items: Any) -> list:
    """Parse section items."""
    if section_type == "channels":
        return parse_enabled_values(raw_items)
    if section_type == "access_points":
        return parse_access_points(raw_items)
    if key == "historical_periods":
        return parse_historical_periods(raw_items)
    if key == "document_types":
        return parse_document_types(raw_items)
    return parse_enabled_values(raw_items)


def parse_channels(data: dict) -> list[HelpOfferEnabledValue]:
    """Parse channels."""
    return parse_enabled_values(data.get("channels"))


def string_or_empty(value: Any) -> str:
    """String or empty."""
    return value if isinstance(value, str) else ""


def optional_int(value: Any) -> int | None:
    """Optional int."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def int_or_default(value: Any, default: int) -> int:
    """Int or default."""
    parsed = optional_int(value)
    return default if parsed is None else parsed
