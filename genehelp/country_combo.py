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

"""Reusable GTK combobox helpers for country selection."""

from typing import Callable, Optional

import gi

gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
from gi.repository import Gtk

from genehelp.country_utils import (
    COUNTRY_DROPDOWN_LIMIT,
    UNKNOWN_COUNTRY_LABEL,
    country_completion_match,
    country_display,
    country_match_sort_key,
    country_matches_query,
    country_sort_key,
    normalize_country_code,
)
from genehelp.l10n import _
from genehelp.models import CountryOption


class CountryCombo(Gtk.ComboBox):
    """Editable GTK country dropdown with lazy loading and search-friendly filtering.
    The widget stores ISO country codes while displaying localized country names.
    """

    def __init__(
        self,
        initial_country_code: str = "",
        on_countries_needed: Optional[Callable[[], list[CountryOption]]] = None,
        on_changed: Optional[Callable] = None,
        placeholder_text: str = "",
    ) -> None:
        """Initialize the object."""
        Gtk.ComboBox.__init__(self, has_entry=True)
        self.on_countries_needed = on_countries_needed
        self.on_changed = on_changed
        self.model = Gtk.ListStore(str, str, str)
        self.all_countries: list[CountryOption] = []
        self.model_updates_enabled = True
        self.countries_request_pending = False
        self.default_country_code = normalize_country_code(initial_country_code)
        self.placeholder_text = placeholder_text or _("Recommended, but can be left empty")

        self.set_model(self.model)
        self.set_entry_text_column(2)
        self.set_hexpand(True)
        self.set_popup_fixed_width(False)

        entry = self.get_child()
        if isinstance(entry, Gtk.Entry):
            entry.set_width_chars(28)
            entry.set_placeholder_text(self.placeholder_text)
            entry.set_completion(self.country_completion())
            entry.connect("changed", self.on_entry_changed)
            entry.connect("button-press-event", self.on_entry_button_press)

        self.connect("changed", self.on_combo_changed)
        self.connect("popup", self.on_combo_popup)
        self.connect("button-press-event", self.on_combo_button_press)
        self.connect("notify::popup-shown", self.on_popup_shown)
        self.set_countries([])

    def country_completion(self) -> Gtk.EntryCompletion:
        """Build country entry completion."""
        completion = Gtk.EntryCompletion()
        completion.set_model(self.model)
        completion.set_text_column(2)
        completion.set_inline_completion(True)
        completion.set_popup_completion(True)
        completion.set_match_func(country_completion_match)
        return completion

    def country_options_loaded(self) -> bool:
        """Return whether country options are loaded."""
        return bool(self.all_countries)

    def set_countries(self, countries: list[CountryOption]) -> None:
        """Set available country options."""
        self.all_countries = sorted(countries, key=country_sort_key)
        self.refresh_model("", self.default_country_code)
        if self.default_country_code:
            self.select_country_code(self.default_country_code)
        else:
            self.clear_country_selection()

    def selected_country_code(self) -> str:
        """Selected country code."""
        active_iter = self.get_active_iter()
        if active_iter is not None:
            return self.model[active_iter][0]

        entry = self.get_child()
        if not isinstance(entry, Gtk.Entry):
            return ""

        typed = entry.get_text().strip()
        if not typed or typed == UNKNOWN_COUNTRY_LABEL:
            return ""

        typed_casefold = typed.casefold()
        for country in self.all_countries:
            code = country.code
            name = country.name
            display = country_display(country)
            if typed_casefold in (
                code.casefold(),
                name.casefold(),
                display.casefold(),
            ):
                return code
        return ""

    def select_country_code(self, country_code: str) -> None:
        """Select country code."""
        normalized = normalize_country_code(country_code)
        if not normalized:
            self.clear_country_selection()
            return

        self.refresh_model("", normalized)
        for index, row in enumerate(self.model):
            if row[0] == normalized:
                self.set_active(index)
                return

        self.clear_country_selection()

    def refresh_model(self, filter_text: str, selected_code: str = "") -> None:
        """Refresh model."""
        entry = self.get_child()
        entry_text = entry.get_text() if isinstance(entry, Gtk.Entry) else ""
        normalized_selected_code = normalize_country_code(selected_code)
        countries = self.visible_countries(filter_text, normalized_selected_code)

        self.model_updates_enabled = False
        try:
            self.model.clear()
            self.model.append(["", UNKNOWN_COUNTRY_LABEL, UNKNOWN_COUNTRY_LABEL])
            for country in countries:
                self.model.append([country.code, country.name, country_display(country)])

            if normalized_selected_code:
                self.set_active(-1)
                for index, row in enumerate(self.model):
                    if row[0] == normalized_selected_code:
                        self.set_active(index)
                        break
            else:
                self.set_active(-1)
                if isinstance(entry, Gtk.Entry):
                    entry.set_text(entry_text)
        finally:
            self.model_updates_enabled = True

    def visible_countries(
        self,
        filter_text: str,
        selected_code: str,
    ) -> list[CountryOption]:
        """Visible countries."""
        query = (filter_text or "").strip()
        selected_country = self.country_by_code(selected_code)
        matches = sorted(
            self.all_countries,
            key=lambda country: country_match_sort_key(country, query),
        )
        if query:
            matches = [country for country in matches if country_matches_query(country, query)]

        visible_limit = max(0, COUNTRY_DROPDOWN_LIMIT - 1)
        visible: list[CountryOption] = []
        if selected_country is not None:
            visible.append(selected_country)

        for country in matches:
            if len(visible) >= visible_limit:
                break
            if selected_country is not None and country.code == selected_country.code:
                continue
            visible.append(country)

        return visible

    def country_by_code(self, country_code: str) -> Optional[CountryOption]:
        """Country by code."""
        normalized = normalize_country_code(country_code)
        if not normalized:
            return None
        for country in self.all_countries:
            if country.code == normalized:
                return country
        return None

    def clear_country_selection(self) -> None:
        """Clear the selected country value."""
        self.set_active(-1)
        entry = self.get_child()
        if isinstance(entry, Gtk.Entry):
            entry.set_text("")

    def on_entry_changed(self, entry: Gtk.Entry) -> None:
        """Handle entry changed."""
        if self.model_updates_enabled:
            self.refresh_model(entry.get_text(), "")
        self.emit_changed_callback()

    def on_combo_changed(self, _combo) -> None:
        """Handle combo changed."""
        self.emit_changed_callback()

    def on_combo_popup(self, _combo) -> None:
        """Handle combo popup."""
        self.load_countries_if_needed()

    def on_combo_button_press(self, _combo, _event) -> bool:
        """Handle combo button press."""
        self.load_countries_if_needed()
        return False

    def on_entry_button_press(self, _entry, _event) -> bool:
        """Handle entry button press."""
        self.load_countries_if_needed()
        return False

    def on_popup_shown(self, combo, _pspec) -> None:
        """Handle popup shown."""
        if combo.get_property("popup-shown"):
            self.load_countries_if_needed()

    def load_countries_if_needed(self) -> None:
        """Load country options on first interaction."""
        if self.country_options_loaded() or self.on_countries_needed is None:
            return
        countries = self.on_countries_needed()
        if countries:
            self.set_countries(countries)

    def emit_changed_callback(self) -> None:
        """Emit the optional changed callback."""
        if self.on_changed is not None:
            self.on_changed(self)

    def get_value(self) -> str:
        """Return value."""
        return self.selected_country_code()
