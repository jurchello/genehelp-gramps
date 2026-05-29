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

"""Country combobox behavior for the GeneHelp GTK UI."""

from typing import Optional

import gi

gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
from gi.repository import GLib, Gtk

from genehelp.country_utils import (
    country_completion_match,
    country_display,
    country_match_sort_key,
    country_matches_query,
    country_sort_key,
    normalize_country_code,
)
from genehelp.l10n import _
from genehelp.models import CountryOption


class CountryUiMixin:
    """Manages country combobox loading, filtering, selection, and display names."""

    def request_country_code(self) -> str:
        """Request country code."""
        return self.selected_country_code(self.request_country_combo)

    def helper_country_code(self) -> str:
        """Helper country code."""
        return self.selected_country_code(self.helper_country_combo)

    def country_options_loaded(self) -> bool:
        """Return whether country options are loaded."""
        return bool(self.all_countries)

    def set_countries(self, countries: list[CountryOption]) -> None:
        """Set available country options."""
        self.all_countries = sorted(countries, key=country_sort_key)
        self.refresh_country_model(
            self.request_country_combo,
            "",
            self.default_request_country_code,
        )
        self.refresh_country_model(self.helper_country_combo, "", "")
        self.select_country_code(
            self.request_country_combo,
            self.default_request_country_code,
        )
        self.clear_country_selection(self.helper_country_combo)
        self.notify_form_changed()

    def set_default_request_country_code(self, country_code: str) -> None:
        """Set the default request country code."""
        self.default_request_country_code = normalize_country_code(country_code)
        if self.country_options_loaded():
            self.select_country_code(
                self.request_country_combo,
                self.default_request_country_code,
            )
            self.notify_form_changed()

    def on_country_changed(self, widget) -> None:
        """Handle country changed."""
        if isinstance(widget, Gtk.Entry):
            combo = self.country_combo_for_entry(widget)
            if combo is not None and self.country_model_updates_enabled:
                self.refresh_country_model(combo, widget.get_text(), "")
        self.notify_form_changed()

    def on_country_popup_shown(self, combo, _pspec) -> None:
        """Handle country popup shown."""
        if combo.get_property("popup-shown"):
            self.request_country_options()

    def request_country_options(self) -> None:
        """Request country options if they are missing."""
        if (
            not self.form_change_callbacks_enabled
            or self.country_options_loaded()
            or self.country_options_request_pending
        ):
            return

        self.country_options_request_pending = True
        GLib.idle_add(self.emit_countries_needed)

    def emit_countries_needed(self) -> bool:
        """Request country loading from the owner."""
        self.country_options_request_pending = False
        if self.form_change_callbacks_enabled and not self.country_options_loaded():
            self.on_countries_needed()
        return False

    def configure_country_combo(
        self,
        combo: Gtk.ComboBox,
        model: Gtk.ListStore,
    ) -> None:
        """Configure a country dropdown widget."""
        combo.set_model(model)
        combo.set_entry_text_column(2)
        entry = combo.get_child()
        if isinstance(entry, Gtk.Entry):
            entry.set_completion(self.country_completion(model))
            entry.set_width_chars(28)
            entry.set_placeholder_text(_("Recommended, but can be left empty"))
            entry.connect("changed", self.on_country_changed)

    def country_name_for_code(self, country_code: str) -> str:
        """Country name for code."""
        if not country_code:
            return _("No country")
        for country in self.all_countries:
            if country.code == country_code:
                return country.name
        return country_code

    def country_completion(self, model: Gtk.ListStore) -> Gtk.EntryCompletion:
        """Build country entry completion."""
        completion = Gtk.EntryCompletion()
        completion.set_model(model)
        completion.set_text_column(2)
        completion.set_inline_completion(True)
        completion.set_popup_completion(True)
        completion.set_match_func(country_completion_match)
        return completion

    def selected_country_code(self, combo: Gtk.ComboBox) -> str:
        """Selected country code."""
        active_iter = combo.get_active_iter()
        if active_iter is not None:
            return self.country_model_for_combo(combo)[active_iter][0]

        entry = combo.get_child()
        if not isinstance(entry, Gtk.Entry):
            return ""

        typed = entry.get_text().strip()
        if not typed or typed == self.UNKNOWN_COUNTRY_LABEL:
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

    def select_country_code(self, combo: Gtk.ComboBox, country_code: str) -> None:
        """Select country code."""
        normalized = normalize_country_code(country_code)
        if not normalized:
            self.clear_country_selection(combo)
            return

        self.refresh_country_model(combo, "", normalized)
        model = self.country_model_for_combo(combo)
        for index, row in enumerate(model):
            if row[0] == normalized:
                combo.set_active(index)
                return

        self.clear_country_selection(combo)

    def refresh_country_model(
        self,
        combo: Gtk.ComboBox,
        filter_text: str,
        selected_code: str,
    ) -> None:
        """Refresh country model."""
        model = self.country_model_for_combo(combo)
        entry = combo.get_child()
        entry_text = entry.get_text() if isinstance(entry, Gtk.Entry) else ""
        normalized_selected_code = normalize_country_code(selected_code)
        countries = self.visible_countries(filter_text, normalized_selected_code)

        self.country_model_updates_enabled = False
        try:
            model.clear()
            model.append(
                [
                    "",
                    self.UNKNOWN_COUNTRY_LABEL,
                    self.UNKNOWN_COUNTRY_LABEL,
                ]
            )
            for country in countries:
                model.append(
                    [
                        country.code,
                        country.name,
                        country_display(country),
                    ]
                )

            if normalized_selected_code:
                combo.set_active(-1)
                for index, row in enumerate(model):
                    if row[0] == normalized_selected_code:
                        combo.set_active(index)
                        break
            else:
                combo.set_active(-1)
                if isinstance(entry, Gtk.Entry):
                    entry.set_text(entry_text)
        finally:
            self.country_model_updates_enabled = True

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

        visible_limit = max(0, self.COUNTRY_DROPDOWN_LIMIT - 1)
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

    def country_model_for_combo(self, combo: Gtk.ComboBox) -> Gtk.ListStore:
        """Country model for combo."""
        if combo is self.request_country_combo:
            return self.request_country_model
        return self.helper_country_model

    def country_combo_for_entry(self, entry: Gtk.Entry) -> Optional[Gtk.ComboBox]:
        """Country combo for entry."""
        for combo in (self.request_country_combo, self.helper_country_combo):
            if combo.get_child() is entry:
                return combo
        return None

    def clear_country_selection(self, combo: Gtk.ComboBox) -> None:
        """Clear the selected country value."""
        combo.set_active(-1)
        entry = combo.get_child()
        if isinstance(entry, Gtk.Entry):
            entry.set_text("")
