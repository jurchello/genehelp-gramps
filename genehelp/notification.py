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

"""GTK toast notification widgets for the GeneHelp gramplet."""

import gi

gi.require_version("Gdk", "3.0")  # pylint: disable=wrong-import-position
gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
from gi.repository import Gdk, GObject, Gtk, Pango


class Notification(Gtk.Window):
    """Temporary floating notification window for explicitly approved messages."""

    def __init__(
        self,
        message: str,
        notification_type: str = "success",
        timeout_ms: int = 4000,
    ) -> None:
        """Initialize the object."""
        super().__init__()

        self.notification_type = notification_type
        self.set_name(self._window_name(notification_type))
        self._configure_window()
        self._build_content(message)
        self.show_all()
        self._position_top_right()
        GObject.timeout_add(timeout_ms, self.close_window)

    def _configure_window(self) -> None:
        """Configure window."""
        screen = Gdk.Screen.get_default()
        if screen is not None:
            visual = screen.get_rgba_visual()
            if visual:
                self.set_visual(visual)

        self.set_decorated(False)
        self.set_accept_focus(False)
        self.set_keep_above(True)
        self.set_size_request(360, -1)

    def _build_content(self, message: str) -> None:
        """Build content."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        box.get_style_context().add_class("genehelp-notification-content")

        label = Gtk.Label(label=message)
        label.get_style_context().add_class("genehelp-notification-label")
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_max_width_chars(42)
        label.set_lines(4)
        label.set_ellipsize(Pango.EllipsizeMode.END)

        box.pack_start(label, True, True, 0)
        self.add(box)

    def _position_top_right(self) -> None:
        """Position top right."""
        screen = Gdk.Screen.get_default()
        if screen is None:
            return

        while Gtk.events_pending():
            Gtk.main_iteration_do(False)

        monitor = screen.get_monitor_geometry(0)
        width, _height = self.get_size()
        self.move(monitor.x + monitor.width - width - 12, monitor.y + 12)

    def close_window(self) -> bool:
        """Close the notification window."""
        self.destroy()
        return False

    @staticmethod
    def _window_name(notification_type: str) -> str:
        """Window name."""
        if notification_type == "error":
            return "NotificationWindowError"
        return "NotificationWindowSuccess"


class NotificationCenter:
    """Small facade that keeps notification usage explicit in call sites."""

    def show(
        self,
        message: str,
        notification_type: str = "success",
        timeout_ms: int = 4000,
    ) -> Notification:
        """Show."""
        return Notification(message, notification_type, timeout_ms)
