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

"""Small Markdown renderer for the GeneHelp GTK text view."""

import re
import webbrowser

import gi

gi.require_version("Gdk", "3.0")  # pylint: disable=wrong-import-position
gi.require_version("Gtk", "3.0")  # pylint: disable=wrong-import-position
from gi.repository import Gdk, Gtk, Pango


class MarkdownRenderer:
    """Render a small Markdown subset into a Gtk.TextView."""

    def __init__(self, text_view: Gtk.TextView) -> None:
        """Initialize the object."""
        self.text_view = text_view
        self.buffer = text_view.get_buffer()
        self._setup_tags()
        self.text_view.connect("motion-notify-event", self.on_hover_link)
        self.text_view.connect("button-release-event", self.on_click_link)

    def _setup_tags(self) -> None:
        """Setup tags."""
        # Gtk.TextTag properties are content formatting, not widget CSS.
        self.heading_tags = {
            1: self.buffer.create_tag("markdown_h1", weight=Pango.Weight.BOLD, scale=1.45),
            2: self.buffer.create_tag("markdown_h2", weight=Pango.Weight.BOLD, scale=1.2),
        }
        self.bold_tag = self.buffer.create_tag(
            "markdown_bold",
            weight=Pango.Weight.BOLD,
        )
        self.italic_tag = self.buffer.create_tag(
            "markdown_italic",
            style=Pango.Style.ITALIC,
        )
        self.underline_tag = self.buffer.create_tag(
            "markdown_underline",
            underline=Pango.Underline.SINGLE,
        )
        self.color_tags = {
            "red": self.buffer.create_tag("markdown_red", foreground="red"),
            "blue": self.buffer.create_tag("markdown_blue", foreground="blue"),
            "green": self.buffer.create_tag("markdown_green", foreground="green"),
            "orange": self.buffer.create_tag("markdown_orange", foreground="orange"),
            "purple": self.buffer.create_tag("markdown_purple", foreground="purple"),
            "yellow": self.buffer.create_tag("markdown_yellow", foreground="goldenrod"),
            "gray": self.buffer.create_tag("markdown_gray", foreground="gray"),
            "black": self.buffer.create_tag("markdown_black", foreground="black"),
        }
        self.link_hover_tag = self.buffer.create_tag(
            "link_hover",
            foreground="green",
            underline=Pango.Underline.SINGLE,
        )

    def render(self, text: str) -> None:
        """Render."""
        self.buffer.set_text("")
        for line in text.splitlines(keepends=True):
            self._render_line(line)

    def _render_line(self, line: str) -> None:
        """Render line."""
        heading_match = re.match(r"^(#{1,2})\s+(.+?)(\n?)$", line)
        if heading_match:
            level = len(heading_match.group(1))
            content = heading_match.group(2).strip()
            newline = heading_match.group(3)
            self.buffer.insert_with_tags(
                self.buffer.get_end_iter(),
                content,
                self.heading_tags[level],
            )
            self.buffer.insert(self.buffer.get_end_iter(), newline)
            return

        self._render_inline(line)

    def _render_inline(self, text: str) -> None:
        """Render inline."""
        token_re = re.compile(
            r"(\*\*.+?\*\*|__.+?__|\*[^*\n]+?\*|"
            r"\{(?:red|blue|green|orange|purple|yellow|gray|black)\|.+?\}|"
            r"\[[^\[\]\n]+?\]\(https?://[^\s)]+?\))"
        )
        position = 0
        for match in token_re.finditer(text):
            if match.start() > position:
                self.buffer.insert(self.buffer.get_end_iter(), text[position : match.start()])
            self._render_token(match.group(0))
            position = match.end()

        if position < len(text):
            self.buffer.insert(self.buffer.get_end_iter(), text[position:])

    def _render_token(self, token: str) -> None:
        """Render token."""
        if token.startswith("**") and token.endswith("**"):
            self._insert_tagged(token[2:-2], self.bold_tag)
            return

        if token.startswith("__") and token.endswith("__"):
            self._insert_tagged(token[2:-2], self.underline_tag)
            return

        if token.startswith("*") and token.endswith("*"):
            self._insert_tagged(token[1:-1], self.italic_tag)
            return

        color_match = re.match(
            r"^\{(red|blue|green|orange|purple|yellow|gray|black)\|(.+?)\}$",
            token,
        )
        if color_match:
            self._insert_tagged(color_match.group(2), self.color_tags[color_match.group(1)])
            return

        link_match = re.match(r"^\[([^\[\]\n]+?)\]\((https?://[^\s)]+?)\)$", token)
        if link_match:
            self._insert_link(link_match.group(1), link_match.group(2))
            return

        self.buffer.insert(self.buffer.get_end_iter(), token)

    def _insert_tagged(self, text: str, tag: Gtk.TextTag) -> None:
        """Insert tagged."""
        if text:
            self.buffer.insert_with_tags(self.buffer.get_end_iter(), text, tag)

    def _insert_link(self, text: str, url: str) -> None:
        """Insert link."""
        tag_name = f"link_{abs(hash(url))}"
        tag_table = self.buffer.get_tag_table()
        link_tag = tag_table.lookup(tag_name)
        if link_tag is None:
            link_tag = self.buffer.create_tag(
                tag_name,
                foreground="blue",
                underline=Pango.Underline.SINGLE,
            )
            link_tag.url = url

        self.buffer.insert_with_tags(self.buffer.get_end_iter(), text, link_tag)

    def on_hover_link(self, widget: Gtk.TextView, event) -> None:
        """Handle hover link."""
        text_window = widget.get_window(Gtk.TextWindowType.TEXT)
        if text_window is None:
            return

        tag = self._link_tag_at_event(widget, event)
        if tag is None:
            text_window.set_cursor(Gdk.Cursor.new(Gdk.CursorType.ARROW))
            self.buffer.remove_tag(
                self.link_hover_tag,
                self.buffer.get_start_iter(),
                self.buffer.get_end_iter(),
            )
            return

        text_window.set_cursor(Gdk.Cursor.new(Gdk.CursorType.HAND1))
        start_iter = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        success, hover_iter = widget.get_iter_at_location(int(event.x), int(event.y))
        if success:
            start_iter = hover_iter.copy()
            start_iter.backward_to_tag_toggle(tag)
            end_iter = hover_iter.copy()
            end_iter.forward_to_tag_toggle(tag)
            self.buffer.apply_tag(self.link_hover_tag, start_iter, end_iter)

    def on_click_link(self, widget: Gtk.TextView, event) -> bool:
        """Handle click link."""
        tag = self._link_tag_at_event(widget, event)
        if tag is None:
            return False

        url = getattr(tag, "url", "")
        if url:
            webbrowser.open(url)
            return True
        return False

    @staticmethod
    def _link_tag_at_event(widget: Gtk.TextView, event):
        """Link tag at event."""
        success, iter_ = widget.get_iter_at_location(int(event.x), int(event.y))
        if not success:
            return None

        for tag in iter_.get_tags():
            if hasattr(tag, "url"):
                return tag
        return None
