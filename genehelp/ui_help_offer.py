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

"""Help profile rendering for the GeneHelp GTK UI."""

from typing import Any

import gi

gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
from gi.repository import Gtk, Pango

from genehelp.l10n import _
from genehelp.models import (
    HelpOffer,
    HelpOfferAccessPoint,
    HelpOfferDocumentType,
    HelpOfferEnabledValue,
    HelpOfferHistoricalPeriod,
    HelpOfferSection,
)


class HelpOfferViewMixin:
    """Renders the public help profile tab inside the gramplet UI."""

    def on_help_offer_retry_clicked(self, _button) -> None:
        """Handle help offer retry clicked."""
        self.on_help_offer_needed()

    def on_help_offer_refresh_clicked(self, _button) -> None:
        """Handle help offer refresh clicked."""
        self.on_help_offer_refresh()

    def set_help_offer(self, offer: HelpOffer) -> None:
        """Set help offer."""
        self.show_help_offer_content()
        self.clear_box(self.help_offer_content_box)
        self.help_offer_content_box.pack_start(
            self.help_offer_header(offer),
            False,
            False,
            0,
        )
        self.set_help_offer_refresh_visible(True)
        self.set_help_offer_profile_button(offer.profile_url)

        if not has_help_offer_content(offer):
            self.help_offer_content_box.pack_start(
                self.help_offer_empty_state(),
                False,
                False,
                12,
            )
            self.help_offer_content_box.show_all()
            return

        for section in offer.sections:
            self.pack_help_offer_section(section)
        self.help_offer_content_box.show_all()

    def set_help_offer_profile_button(self, profile_url: str) -> None:
        """Set help offer profile button."""
        self.help_offer_profile_url = profile_url
        self.set_widget_visible(self.help_offer_profile_button, bool(profile_url))
        self.sync_help_offer_footer_visibility()

    def set_help_offer_refresh_visible(self, visible: bool) -> None:
        """Set help offer refresh button visibility."""
        self.set_widget_visible(self.help_offer_refresh_button, visible)
        self.sync_help_offer_footer_visibility()

    def sync_help_offer_footer_visibility(self) -> None:
        """Show the help offer footer when it has at least one visible action."""
        self.set_widget_visible(
            self.help_offer_footer_box,
            bool(self.help_offer_profile_url)
            or not self.help_offer_refresh_button.get_no_show_all(),
        )

    def show_help_offer_content(self) -> None:
        """Show help offer content."""
        self.show_content_or_error(
            self.help_offer_content_scroller,
            self.help_offer_error_box,
            True,
        )

    def show_help_offer_error(self) -> None:
        """Show help offer error."""
        self.set_help_offer_profile_button("")
        self.set_help_offer_refresh_visible(False)
        self.show_content_or_error(
            self.help_offer_content_scroller,
            self.help_offer_error_box,
            False,
        )

    def on_help_offer_profile_button_clicked(self, _button) -> None:
        """Handle help offer profile button clicked."""
        if self.help_offer_profile_url:
            self.on_help_offer_profile_open(self.help_offer_profile_url)

    def pack_help_offer_tag_section(self, title: str, items: list[str]) -> None:
        """Pack help offer tag section."""
        if not items:
            return
        self.help_offer_content_box.pack_start(
            self.help_offer_tag_section(title, items),
            False,
            False,
            0,
        )

    def pack_help_offer_section(self, section: HelpOfferSection) -> None:
        """Pack help offer section."""
        if section.type == "single_choice":
            selected_label = help_offer_selected_value_label(section.items)
            if selected_label:
                self.help_offer_content_box.pack_start(
                    self.help_offer_text_section(section.label, selected_label),
                    False,
                    False,
                    0,
                )
            return

        if section.type == "channels":
            channel_items = help_offer_channel_items(section.items)
            if channel_items:
                self.help_offer_content_box.pack_start(
                    self.help_offer_channel_section(section.label, channel_items),
                    False,
                    False,
                    0,
                )
            return

        if section.type == "access_points":
            access_points = help_offer_access_point_items(section.items)
            if access_points:
                self.help_offer_content_box.pack_start(
                    self.help_offer_access_points_section(section.label, access_points),
                    False,
                    False,
                    0,
                )
            return

        if section.key == "historical_periods":
            periods = help_offer_historical_period_items(section.items)
            if periods:
                self.help_offer_content_box.pack_start(
                    self.help_offer_historical_period_section(section.label, periods),
                    False,
                    False,
                    0,
                )
            return

        self.pack_help_offer_tag_section(
            section.label,
            help_offer_tag_labels(section),
        )

    def help_offer_header(self, offer: HelpOffer) -> Gtk.Widget:
        """Help offer header."""
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        country_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        country_row.set_hexpand(True)
        country_row.pack_start(
            self.help_offer_text_section(
                _("Helper country"),
                self.help_offer_country_name(offer.helper_country_code),
            ),
            False,
            False,
            0,
        )
        header.pack_start(country_row, False, False, 0)
        return header

    def help_offer_channel_section(self, title: str, items: list[tuple[str, str]]):
        """Help offer channel section."""
        section = self.help_offer_section(title)
        if not items:
            return section
        list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        for label, description in items:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            self.add_css_class(row, "genehelp-public-channel-item")
            bullet = Gtk.Label(label="•")
            bullet.set_xalign(0)
            bullet.set_yalign(0)
            self.add_css_class(bullet, "genehelp-public-channel-bullet")
            row.pack_start(bullet, False, False, 0)

            content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            channel_label = Gtk.Label(label=label)
            channel_label.set_xalign(0)
            self.add_css_class(channel_label, "genehelp-public-channel-title")
            content.pack_start(channel_label, False, False, 0)
            if description:
                small = Gtk.Label(label=description)
                small.set_xalign(0)
                small.set_line_wrap(True)
                small.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
                self.add_css_class(small, "genehelp-muted")
                content.pack_start(small, False, False, 0)
            row.pack_start(content, True, True, 0)
            list_box.pack_start(row, False, False, 0)
        section.pack_start(list_box, False, False, 0)
        return section

    def help_offer_access_points_section(
        self,
        title: str,
        access_points: list[HelpOfferAccessPoint],
    ) -> Gtk.Widget:
        """Help offer access points section."""
        section = self.help_offer_section(title)
        if not access_points:
            return section

        list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
        self.add_css_class(list_box, "genehelp-public-location-list")
        for access_point in access_points:
            item = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            self.add_css_class(item, "genehelp-public-location-item")
            bullet = Gtk.Label(label="•")
            bullet.set_xalign(0)
            bullet.set_yalign(0)
            self.add_css_class(bullet, "genehelp-public-location-bullet")
            item.pack_start(bullet, False, False, 0)

            content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            territory = Gtk.Label(label=self.access_point_territory_label(access_point))
            territory.set_xalign(0)
            territory.set_line_wrap(True)
            territory.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            self.add_css_class(territory, "genehelp-public-location-title")
            content.pack_start(territory, False, False, 0)

            meta = self.access_point_meta_label(access_point)
            if meta:
                meta_label = Gtk.Label(label=meta)
                meta_label.set_xalign(0)
                meta_label.set_line_wrap(True)
                meta_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
                self.add_css_class(meta_label, "genehelp-public-location-meta")
                content.pack_start(meta_label, False, False, 0)

            item.pack_start(content, True, True, 0)
            list_box.pack_start(item, False, False, 0)

        section.pack_start(list_box, False, False, 0)
        return section

    def help_offer_historical_period_section(
        self,
        title: str,
        periods: list[HelpOfferHistoricalPeriod],
    ) -> Gtk.Widget:
        """Help offer historical period section."""
        section = self.help_offer_section(title)
        if not periods:
            return section

        range_items = historical_period_range_items(periods)
        context_labels = historical_period_context_labels(periods)

        if range_items:
            list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
            self.add_css_class(list_box, "genehelp-historical-period-list")
            for period in range_items:
                item = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                self.add_css_class(item, "genehelp-historical-period-item")
                bullet = Gtk.Label(label="•")
                bullet.set_xalign(0)
                bullet.set_yalign(0)
                self.add_css_class(bullet, "genehelp-historical-period-bullet")
                item.pack_start(bullet, False, False, 0)

                content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                period_title = Gtk.Label(label=historical_period_title(period))
                period_title.set_xalign(0)
                period_title.set_line_wrap(True)
                period_title.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
                self.add_css_class(period_title, "genehelp-historical-period-title")
                content.pack_start(period_title, False, False, 0)

                meta = historical_period_meta(period)
                if meta:
                    meta_label = Gtk.Label(label=meta)
                    meta_label.set_xalign(0)
                    meta_label.set_line_wrap(True)
                    meta_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
                    self.add_css_class(meta_label, "genehelp-historical-period-meta")
                    content.pack_start(meta_label, False, False, 0)

                item.pack_start(content, True, True, 0)
                list_box.pack_start(item, False, False, 0)

            section.pack_start(list_box, False, False, 0)

        if context_labels:
            section.pack_start(self.help_offer_tags(context_labels), False, False, 0)

        return section

    def help_offer_tag_section(self, title: str, items: list[str]) -> Gtk.Widget:
        """Help offer tag section."""
        section = self.help_offer_section(title)
        if not items:
            return section

        section.pack_start(self.help_offer_tags(items), False, False, 0)
        return section

    def help_offer_text_section(self, title: str, value: str) -> Gtk.Widget:
        """Help offer text section."""
        section = self.help_offer_section(title)
        text = Gtk.Label(label=value or _("Not specified"))
        text.set_xalign(0)
        text.set_line_wrap(True)
        text.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.add_css_class(text, "genehelp-help-offer-section-text")
        section.pack_start(text, False, False, 0)
        return section

    def help_offer_tags(self, items: list[str]) -> Gtk.Widget:
        """Help offer tags."""
        tags = Gtk.FlowBox()
        tags.set_selection_mode(Gtk.SelectionMode.NONE)
        tags.set_column_spacing(6)
        tags.set_row_spacing(6)
        tags.set_max_children_per_line(4)
        self.add_css_class(tags, "genehelp-tags")
        for item in items:
            tag = Gtk.Label(label=item)
            self.add_css_class(tag, "genehelp-tag")
            tags.add(tag)
        return tags

    def help_offer_section(self, title: str) -> Gtk.Box:
        """Help offer section."""
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.add_css_class(section, "genehelp-show-section")
        heading = Gtk.Label(label=title)
        heading.set_xalign(0)
        self.add_css_class(heading, "genehelp-help-offer-section-title")
        section.pack_start(heading, False, False, 0)
        return section

    def help_offer_meta_chip(self, label: str, value: str) -> Gtk.Widget:
        """Help offer meta chip."""
        chip = Gtk.Label(label=f"{label}: {value or _('Not specified')}")
        chip.set_xalign(0)
        self.add_css_class(chip, "genehelp-help-offer-meta-chip")
        return chip

    def help_offer_empty_state(self) -> Gtk.Widget:
        """Help offer empty state."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.add_css_class(box, "genehelp-empty-state")
        title = Gtk.Label(label=_("Help profile is not filled in yet"))
        title.set_xalign(0)
        self.add_css_class(title, "genehelp-help-offer-section-title")
        box.pack_start(title, False, False, 0)
        return box

    def access_point_territory_label(self, access_point: HelpOfferAccessPoint) -> str:
        """Access point territory label."""
        if access_point.location_type == "country":
            return self.country_name_for_code(access_point.country_code)

        if access_point.region_wide and access_point.administrative_area_name:
            country_name = self.country_name_for_code(access_point.country_code)
            return f"{access_point.administrative_area_name}, {country_name}"

        parts = [
            access_point.place_name,
            access_point.district,
            access_point.region,
            self.country_name_for_code(access_point.country_code),
        ]
        return ", ".join([part for part in parts if part]) or _("Not specified")

    def access_point_meta_label(self, access_point: HelpOfferAccessPoint) -> str:
        """Access point meta label."""
        parts = []
        if access_point.location_type_label:
            parts.append(access_point.location_type_label)
        elif access_point.location_type == "country":
            parts.append(_("Whole country"))
        if access_point.region_wide:
            parts.append(_("Whole region"))
        if access_point.radius_km:
            parts.append(_("Radius: %d km") % access_point.radius_km)
        object_label = access_point_object_label(access_point)
        if object_label:
            parts.append(object_label)
        if not parts and access_point.location_type == "place":
            parts.append(_("Whole locality"))
        return " · ".join(parts)

    def help_offer_country_name(self, country_code: str) -> str:
        """Help offer country name."""
        if not country_code:
            return _("Not specified")
        return self.country_name_for_code(country_code)


def has_help_offer_content(offer: HelpOffer) -> bool:
    """Return whether help offer content."""
    return any(section_has_content(section) for section in offer.sections)


def section_has_content(section: HelpOfferSection) -> bool:
    """Section has content."""
    if section.type == "access_points":
        return bool(help_offer_access_point_items(section.items))
    if section.type == "channels":
        return bool(help_offer_channel_items(section.items))
    if section.key == "historical_periods":
        periods = help_offer_historical_period_items(section.items)
        return bool(
            historical_period_range_items(periods) or historical_period_context_labels(periods)
        )
    return bool(help_offer_tag_labels(section))


def help_offer_channel_items(raw_items: tuple[Any, ...]) -> list[tuple[str, str]]:
    """Help offer channel items."""
    items = []
    for channel in raw_items:
        if not isinstance(channel, HelpOfferEnabledValue):
            continue
        if channel.enabled and channel.label:
            items.append((channel.label, channel.description))
    return items


def help_offer_access_point_items(raw_items: tuple[Any, ...]) -> list[HelpOfferAccessPoint]:
    """Help offer access point items."""
    return [item for item in raw_items if isinstance(item, HelpOfferAccessPoint)]


def help_offer_historical_period_items(
    raw_items: tuple[Any, ...],
) -> list[HelpOfferHistoricalPeriod]:
    """Help offer historical period items."""
    return [
        item for item in raw_items if isinstance(item, HelpOfferHistoricalPeriod) and item.enabled
    ]


def historical_period_range_items(
    periods: list[HelpOfferHistoricalPeriod],
) -> list[HelpOfferHistoricalPeriod]:
    """Historical period range items."""
    return [
        period
        for period in periods
        if period.selection_type in ("range_preset", "custom_range")
        and historical_period_title(period)
    ]


def historical_period_context_labels(periods: list[HelpOfferHistoricalPeriod]) -> list[str]:
    """Historical period context labels."""
    return [
        historical_period_title(period)
        for period in periods
        if period.selection_type == "historical_context" and historical_period_title(period)
    ]


def help_offer_tag_labels(section: HelpOfferSection) -> list[str]:
    """Help offer tag labels."""
    if section.key == "document_types":
        return document_type_labels(
            tuple(item for item in section.items if isinstance(item, HelpOfferDocumentType))
        )
    return enabled_value_labels(
        tuple(item for item in section.items if isinstance(item, HelpOfferEnabledValue))
    )


def historical_period_title(period: HelpOfferHistoricalPeriod) -> str:
    """Historical period title."""
    if period.label:
        return period.label
    date_range = historical_period_date_range(period)
    if date_range:
        return date_range
    return ""


def historical_period_meta(period: HelpOfferHistoricalPeriod) -> str:
    """Historical period meta."""
    parts = []
    if period.selection_type_label:
        parts.append(period.selection_type_label)
    date_range = historical_period_date_range(period)
    if date_range and date_range != historical_period_title(period):
        parts.append(date_range)
    return " · ".join(parts)


def historical_period_date_range(period: HelpOfferHistoricalPeriod) -> str:
    """Historical period date range."""
    if period.from_year is not None and period.to_year is not None:
        return f"{period.from_year}-{period.to_year}"
    if period.from_year is not None:
        return _("from %d") % period.from_year
    if period.to_year is not None:
        return _("until %d") % period.to_year
    return ""


def document_type_labels(
    document_types: tuple[HelpOfferDocumentType, ...],
) -> list[str]:
    """Document type labels."""
    return [item.label for item in document_types if item.enabled and item.label]


def access_point_object_label(access_point: HelpOfferAccessPoint) -> str:
    """Access point object label."""
    object_type = access_point.object_type_label
    if access_point.object_name and object_type:
        return f"{access_point.object_name} ({object_type})"
    if access_point.object_name:
        return access_point.object_name
    return object_type


def enabled_value_labels(values: tuple[HelpOfferEnabledValue, ...]) -> list[str]:
    """Enabled value labels."""
    return [value.label for value in values if value.enabled and value.label]


def help_offer_selected_value_label(values: tuple[Any, ...]) -> str:
    """Help offer selected value label."""
    for value in values:
        if isinstance(value, HelpOfferEnabledValue) and value.enabled:
            return value.label
    return ""


def any_enabled(values) -> bool:
    """Return whether any item is enabled."""
    return any(getattr(value, "enabled", False) for value in values)
