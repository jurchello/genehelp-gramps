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

"""Genealogy request list rendering for the GeneHelp GTK UI."""

import gi

gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
from gi.repository import GLib, Gtk, Pango

from genehelp.country_utils import normalize_country_code
from genehelp.l10n import _
from genehelp.models import GenealogyRequestGroup, GenealogyRequestItem


class RequestListMixin:
    """Renders the owner genealogy request list tab and request status badges."""

    def on_requests_retry_clicked(self, _button) -> None:
        """Handle requests retry clicked."""
        self.on_requests_needed()

    def on_requests_refresh_clicked(self, _button) -> None:
        """Handle requests refresh clicked."""
        self.on_requests_refresh()

    def on_request_row_activated(self, tree_view, path, _column) -> None:
        """Handle request row activated."""
        model = tree_view.get_model()
        tree_iter = model.get_iter(path)
        if tree_iter is None:
            return
        is_group = model[tree_iter][6]
        if is_group:
            if tree_view.row_expanded(path):
                tree_view.collapse_row(path)
            else:
                tree_view.expand_row(path, False)
            return

        url = model[tree_iter][5]
        if url:
            self.on_request_activated(url)

    def configure_requests_tree(self) -> None:
        """Configure the genealogy request list tree."""
        self.requests_tree_view.set_model(self.requests_model)
        self.requests_tree_view.set_headers_visible(True)
        self.requests_tree_view.set_activate_on_single_click(False)

        title_renderer = Gtk.CellRendererText()
        title_renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        title_column = Gtk.TreeViewColumn(_("Title"), title_renderer, text=0, weight=7)
        title_column.set_expand(True)
        title_column.set_resizable(True)
        self.requests_tree_view.append_column(title_column)

        status_renderer = Gtk.CellRendererText()
        status_renderer.set_property("xpad", 6)
        status_column = Gtk.TreeViewColumn(
            _("Status"),
            status_renderer,
            markup=2,
        )
        status_column.set_resizable(True)
        self.requests_tree_view.append_column(status_column)

        date_renderer = Gtk.CellRendererText()
        date_column = Gtk.TreeViewColumn(_("Created"), date_renderer, text=4)
        date_column.set_resizable(True)
        self.requests_tree_view.append_column(date_column)

    def set_genealogy_requests(self, groups: list[GenealogyRequestGroup]) -> None:
        """Render genealogy request groups."""
        self.show_content_or_error(self.requests_scroller, self.requests_error_box, True)
        self.set_requests_refresh_visible(True)
        self.requests_model.clear()
        for group in groups:
            country_label = self.country_group_label(group)
            parent_iter = self.requests_model.append(
                None,
                [
                    country_label,
                    "",
                    "",
                    "",
                    "",
                    "",
                    True,
                    Pango.Weight.BOLD,
                ],
            )
            for item in group.items:
                status_label, status_markup = request_item_status_badge(item)
                self.requests_model.append(
                    parent_iter,
                    [
                        item.title,
                        status_label,
                        status_markup,
                        "",
                        display_datetime(item.created_at),
                        item.edit_url or item.url,
                        False,
                        Pango.Weight.NORMAL,
                    ],
                )
        self.expand_first_request_group()

    def show_genealogy_requests_list(self) -> None:
        """Show genealogy requests list."""
        self.show_content_or_error(self.requests_scroller, self.requests_error_box, True)

    def show_genealogy_requests_error(self) -> None:
        """Show genealogy requests error."""
        self.set_requests_refresh_visible(False)
        self.show_content_or_error(self.requests_scroller, self.requests_error_box, False)

    def set_requests_refresh_visible(self, visible: bool) -> None:
        """Set requests refresh footer visibility."""
        self.set_widget_visible(self.requests_footer_box, visible)
        self.set_widget_visible(self.requests_refresh_button, visible)

    def expand_first_request_group(self) -> None:
        """Expand the first request group row."""
        first_iter = self.requests_model.get_iter_first()
        if first_iter is not None:
            first_path = self.requests_model.get_path(first_iter)
            self.requests_tree_view.expand_row(first_path, False)

    def country_group_label(self, group: GenealogyRequestGroup) -> str:
        """Country group label."""
        country_code = normalize_country_code(group.helper_country_code)
        country_name = self.country_name_for_code(country_code)
        return f"{country_name} ({group.count})"


def status_badge(status: str) -> tuple[str, str]:
    """Status badge."""
    normalized = (status or "").strip().lower()
    labels = {
        "draft": _("Draft"),
        "pending": _("Pending"),
        "open": _("Open"),
        "new": _("New"),
        "active": _("Active"),
        "in_progress": _("In progress"),
        "assigned": _("Assigned"),
        "paused": _("Paused"),
        "completed": _("Completed"),
        "resolved": _("Resolved"),
        "closed": _("Closed"),
        "cancelled": _("Cancelled"),
        "canceled": _("Cancelled"),
        "rejected": _("Rejected"),
        "expired": _("Expired"),
    }
    if normalized:
        background, foreground = status_badge_colors(normalized)
        return status_badge_markup(
            labels.get(normalized, status),
            background,
            foreground,
        )
    return "", ""


def request_item_status_badge(item: GenealogyRequestItem) -> tuple[str, str]:
    """Request item status badge."""
    if item.is_test:
        return status_badge_markup(_("Test"), "#ede9fe", "#4c1d95")

    return status_badge(item.status)


def status_badge_colors(status: str) -> tuple[str, str]:
    """Status badge colors."""
    # Gtk.TreeView cells use Pango markup here, so these per-status colors
    # cannot be assigned through normal GTK CSS classes.
    if status in ("draft", "pending", "open", "new"):
        return "#dbeafe", "#1e3a5f"
    if status in ("active", "in_progress", "assigned"):
        return "#dcfce7", "#14532d"
    if status == "paused":
        return "#fef3c7", "#78350f"
    if status in ("completed", "resolved", "closed"):
        return "#e5e7eb", "#374151"
    if status in ("cancelled", "canceled", "rejected", "expired"):
        return "#fee2e2", "#7f1d1d"
    return "#f3f4f6", "#374151"


def status_badge_markup(label: str, background: str, foreground: str) -> tuple[str, str]:
    """Status badge markup."""
    escaped_label = GLib.markup_escape_text(label)
    markup = f'<span background="{background}" foreground="{foreground}">  {escaped_label}  </span>'
    return label, markup


def display_datetime(value: str) -> str:
    """Display datetime."""
    if not value:
        return ""
    return value.replace("T", " ").replace("Z", "")[:16]
