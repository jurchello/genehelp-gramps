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

"""Unit tests for help-offer parsing and presentation helpers."""

from genehelp.help_offer import (
    parse_access_points,
    parse_document_types,
    parse_enabled_values,
    parse_help_offer_response,
    parse_historical_periods,
    parse_section_items,
)
from genehelp.ui_help_offer import (
    access_point_object_label,
    enabled_value_labels,
    help_offer_access_point_items,
    help_offer_channel_items,
    help_offer_historical_period_items,
    help_offer_selected_value_label,
    help_offer_tag_labels,
    historical_period_context_labels,
    historical_period_date_range,
    historical_period_meta,
    historical_period_range_items,
    historical_period_title,
    section_has_content,
)
from genehelp.models import (
    HelpOfferAccessPoint,
    HelpOfferDocumentType,
    HelpOfferEnabledValue,
    HelpOfferHistoricalPeriod,
    HelpOfferSection,
)


def test_help_offer_response_rejects_missing_or_invalid_data() -> None:
    """Verify invalid help-offer response shapes return no profile."""
    assert parse_help_offer_response({}) is None
    assert parse_help_offer_response({"data": []}) is None


def test_enabled_values_parse_string_and_dict_items() -> None:
    """Verify enabled value parsing supports legacy and typed API items."""
    values = parse_enabled_values(
        [
            "remote_help",
            {"key": "offline", "label": "Offline", "description": "In person"},
            {"key": "", "label": "Ignored"},
            42,
        ]
    )

    assert values == [
        HelpOfferEnabledValue(key="remote_help", label="remote_help", enabled=True),
        HelpOfferEnabledValue(
            key="offline",
            label="Offline",
            description="In person",
            enabled=False,
        ),
    ]


def test_document_types_parse_key_aliases_and_invalid_shapes() -> None:
    """Verify document type parsing supports both API key names."""
    document_types = parse_document_types(
        [
            "metric_books",
            {"document_type_key": "censuses", "label": "Censuses", "enabled": False},
            {"key": "revision_lists", "label": "Revision lists"},
            {"label": "Ignored"},
            None,
        ]
    )

    assert document_types == [
        HelpOfferDocumentType(key="metric_books", label="metric_books"),
        HelpOfferDocumentType(key="censuses", label="Censuses", enabled=False),
        HelpOfferDocumentType(key="revision_lists", label="Revision lists"),
    ]


def test_access_points_parse_invalid_radius_as_none() -> None:
    """Verify access point parsing normalizes invalid radius values."""
    access_points = parse_access_points(
        [
            {
                "location_type": "place",
                "country_code": "UA",
                "place_name": "Kyiv",
                "radius_km": "bad",
            },
            "ignored",
        ]
    )

    assert len(access_points) == 1
    assert access_points[0].place_name == "Kyiv"
    assert access_points[0].radius_km is None


def test_historical_periods_parse_invalid_years_as_none() -> None:
    """Verify historical period parsing tolerates invalid years."""
    periods = parse_historical_periods(
        [
            {
                "key": "custom",
                "selection_type": "custom_range",
                "from_year": "bad",
                "to_year": "1917",
            }
        ]
    )

    assert periods[0].from_year is None
    assert periods[0].to_year == 1917


def test_section_item_parser_uses_typed_special_cases_and_fallback() -> None:
    """Verify section item parser dispatches by type and key."""
    assert isinstance(
        parse_section_items("online_area", "access_points", [{"location_type": "country"}])[0],
        HelpOfferAccessPoint,
    )
    assert isinstance(
        parse_section_items("historical_periods", "enabled_values", [{"key": "p"}])[0],
        HelpOfferHistoricalPeriod,
    )
    assert isinstance(
        parse_section_items("document_types", "enabled_values", [{"key": "metric"}])[0],
        HelpOfferDocumentType,
    )
    assert isinstance(
        parse_section_items("capabilities", "unknown", [{"key": "translation"}])[0],
        HelpOfferEnabledValue,
    )


def test_help_offer_content_helpers_filter_enabled_items() -> None:
    """Verify help-offer content helpers only expose renderable enabled items."""
    enabled = HelpOfferEnabledValue("online", "Online", "Remote", True)
    disabled = HelpOfferEnabledValue("offline", "Offline", enabled=False)
    access_point = HelpOfferAccessPoint(location_type="country", country_code="UA")
    period_enabled = HelpOfferHistoricalPeriod(
        key="range",
        selection_type="custom_range",
        label="1800-1900",
        enabled=True,
    )
    period_disabled = HelpOfferHistoricalPeriod(
        key="hidden",
        selection_type="custom_range",
        label="Hidden",
        enabled=False,
    )

    assert help_offer_channel_items((enabled, disabled, "bad")) == [("Online", "Remote")]
    assert help_offer_access_point_items((access_point, enabled)) == [access_point]
    assert help_offer_historical_period_items((period_enabled, period_disabled)) == [period_enabled]
    assert enabled_value_labels((enabled, disabled)) == ["Online"]
    assert help_offer_selected_value_label((disabled, enabled)) == "Online"


def test_historical_period_labels_and_ranges() -> None:
    """Verify historical period title, meta, and grouping helpers."""
    range_period = HelpOfferHistoricalPeriod(
        key="custom",
        selection_type="custom_range",
        selection_type_label="Custom range",
        from_year=1800,
        to_year=1900,
    )
    context_period = HelpOfferHistoricalPeriod(
        key="empire",
        selection_type="historical_context",
        label="Russian Empire",
    )
    from_period = HelpOfferHistoricalPeriod(
        key="from",
        selection_type="custom_range",
        from_year=1850,
    )
    until_period = HelpOfferHistoricalPeriod(
        key="until",
        selection_type="custom_range",
        to_year=1917,
    )

    assert historical_period_title(range_period) == "1800-1900"
    assert historical_period_meta(range_period) == "Custom range"
    assert historical_period_date_range(from_period) == "from 1850"
    assert historical_period_date_range(until_period) == "until 1917"
    assert historical_period_range_items([range_period, context_period]) == [range_period]
    assert historical_period_context_labels([range_period, context_period]) == ["Russian Empire"]


def test_help_offer_tag_labels_and_section_content_detection() -> None:
    """Verify tag label extraction and section content detection."""
    document_section = HelpOfferSection(
        key="document_types",
        label="Documents",
        type="enabled_values",
        items=(
            HelpOfferDocumentType(key="metric_books", label="Metric books"),
            HelpOfferDocumentType(key="censuses", label="Censuses", enabled=False),
        ),
    )
    empty_section = HelpOfferSection(
        key="capabilities",
        label="Capabilities",
        type="enabled_values",
        items=(HelpOfferEnabledValue(key="translation", label="Translation"),),
    )

    assert help_offer_tag_labels(document_section) == ["Metric books"]
    assert section_has_content(document_section) is True
    assert section_has_content(empty_section) is False


def test_access_point_object_label_uses_name_and_type() -> None:
    """Verify access point object label formatting."""
    assert (
        access_point_object_label(
            HelpOfferAccessPoint(
                location_type="place",
                country_code="UA",
                object_name="Central Archive",
                object_type_label="Archive",
            )
        )
        == "Central Archive (Archive)"
    )
    assert (
        access_point_object_label(
            HelpOfferAccessPoint(
                location_type="place",
                country_code="UA",
                object_name="Central Archive",
            )
        )
        == "Central Archive"
    )
    assert (
        access_point_object_label(
            HelpOfferAccessPoint(
                location_type="place",
                country_code="UA",
                object_type_label="Archive",
            )
        )
        == "Archive"
    )
