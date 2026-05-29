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

"""Helpers for reading the active Gramps page and selected object."""

from typing import Any, Optional

from genehelp.themes import PAGE_HANDLERS


class GrampsContext:
    """Adapter around Gramps UI state and database access.
    It hides page detection and active object lookup behind a small interface.
    """

    def __init__(self, gramplet: Any) -> None:
        """Initialize the object."""
        self.gramplet = gramplet

    def detect_nav_type(self) -> Optional[str]:
        """Detect the active Gramps navigation type."""
        try:
            active_page = self.gramplet.gui.uistate.viewmanager.active_page
            navigation_type = active_page.navigation_type()
        except AttributeError:
            return None

        if navigation_type in PAGE_HANDLERS:
            return navigation_type
        return None

    def active_handle(self, nav_type: Optional[str]) -> Optional[str]:
        """Active handle."""
        if not nav_type:
            return None
        try:
            return self.gramplet.gui.uistate.get_active(nav_type)
        except AttributeError:
            return self.gramplet.get_active(nav_type)

    def active_object(self, nav_type: Optional[str], handle: Optional[str] = None) -> Any:
        """Active object."""
        if not nav_type:
            return None
        if handle is None:
            handle = self.active_handle(nav_type)
        if not handle:
            return None

        handler = PAGE_HANDLERS.get(nav_type)
        if handler is None:
            return None

        getter = getattr(self.gramplet.dbstate.db, handler.object_getter_name, None)
        return getter(handle) if getter else None
