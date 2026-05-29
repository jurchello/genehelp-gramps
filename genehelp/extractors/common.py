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

"""Shared extraction helpers for Gramps notes, attributes, and text blocks."""

from typing import Any


def note_texts(db: Any, note_handles) -> list[str]:
    """Note texts."""
    notes = []
    for note_handle in note_handles:
        note = db.get_note_from_handle(note_handle)
        if note:
            note_text = note.get().strip()
            if note_text:
                notes.append(note_text)
    return notes


def attribute_texts(attribute_owner: Any) -> list[str]:
    """Attribute texts."""
    return [
        f"{attribute_type_text(attribute.get_type())}: {attribute.get_value()}"
        for attribute in attribute_owner.get_attribute_list()
    ]


def attribute_type_text(attr_type: Any) -> str:
    """Return a stable text label for regular and source attribute types."""
    type2base = getattr(attr_type, "type2base", None)
    if callable(type2base):
        return str(type2base()).strip()

    string = getattr(attr_type, "string", None)
    if string:
        return str(string).strip()

    return str(attr_type).strip()


def compact_description(blocks: list[list[str]]) -> str:
    """Compact description."""
    return "\n\n".join("\n".join(block) for block in blocks if block)


def titled_block(title: str, lines: list[str]) -> list[str]:
    """Titled block."""
    if not lines:
        return []
    return [title, *lines]


def bullet_texts(items: list[str], prefix: str = "") -> list[str]:
    """Bullet texts."""
    lines = []
    for item in items:
        item_lines = [line.rstrip() for line in item.splitlines() if line.strip()]
        if not item_lines:
            continue
        lines.append(f"{prefix}- {item_lines[0]}")
        lines.extend(f"{prefix}  {line}" for line in item_lines[1:])
    return lines


def prefixed_block_lines(lines: list[str], first_prefix: str = "- ", rest_prefix: str = "  "):
    """Prefixed block lines."""
    if not lines:
        return []
    return [f"{first_prefix}{lines[0]}", *[f"{rest_prefix}{line}" for line in lines[1:]]]


def reference_handle(ref: Any) -> str:
    """Reference handle."""
    if ref is None:
        return ""
    handle = getattr(ref, "ref", "")
    if handle:
        return handle
    get_reference_handle = getattr(ref, "get_reference_handle", None)
    if get_reference_handle is None:
        return ""
    return get_reference_handle() or ""
