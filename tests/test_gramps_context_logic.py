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

"""Unit tests for Gramps context detection and active object lookup."""

import types

from genehelp.config import DATA_SOURCE_MEDIA
from genehelp.gramps_context import GrampsContext


class FakeActivePage:
    """Active page test double."""

    def __init__(self, nav_type: str) -> None:
        """Initialize the test double."""
        self.nav_type = nav_type

    def navigation_type(self) -> str:
        """Return navigation type."""
        return self.nav_type


class FakeDb:
    """Database test double for active object lookup."""

    def __init__(self) -> None:
        """Initialize the test double."""
        self.media = {"media-1": object()}

    def get_media_from_handle(self, handle: str):
        """Return media by handle."""
        return self.media.get(handle)


def gramplet_with_uistate(nav_type: str, active_handle: str):
    """Build a gramplet-like object with uistate lookup."""
    uistate = types.SimpleNamespace(
        viewmanager=types.SimpleNamespace(active_page=FakeActivePage(nav_type)),
        get_active=lambda _nav_type: active_handle,
    )
    gui = types.SimpleNamespace(uistate=uistate)
    return types.SimpleNamespace(gui=gui, dbstate=types.SimpleNamespace(db=FakeDb()))


def test_context_detects_supported_navigation_type() -> None:
    """Verify supported active page navigation type is detected."""
    context = GrampsContext(gramplet_with_uistate(DATA_SOURCE_MEDIA, "media-1"))

    assert context.detect_nav_type() == DATA_SOURCE_MEDIA


def test_context_rejects_unknown_or_missing_navigation_type() -> None:
    """Verify unknown or missing active page navigation type is ignored."""
    assert GrampsContext(gramplet_with_uistate("Unknown", "x")).detect_nav_type() is None
    assert GrampsContext(types.SimpleNamespace()).detect_nav_type() is None


def test_context_active_handle_falls_back_to_gramplet_get_active() -> None:
    """Verify active handle lookup falls back to gramplet get_active."""
    gramplet = types.SimpleNamespace(
        gui=types.SimpleNamespace(uistate=types.SimpleNamespace()),
        get_active=lambda _nav_type: "media-2",
    )

    assert GrampsContext(gramplet).active_handle(DATA_SOURCE_MEDIA) == "media-2"
    assert GrampsContext(gramplet).active_handle(None) is None


def test_context_active_object_uses_registered_getter() -> None:
    """Verify active object lookup uses the page handler getter."""
    gramplet = gramplet_with_uistate(DATA_SOURCE_MEDIA, "media-1")
    context = GrampsContext(gramplet)

    assert context.active_object(DATA_SOURCE_MEDIA) is gramplet.dbstate.db.media["media-1"]
    assert context.active_object(DATA_SOURCE_MEDIA, "missing") is None
    assert context.active_object(None) is None
