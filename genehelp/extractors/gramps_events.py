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

"""Shared Gramps event formatting helpers."""

from dataclasses import dataclass
from typing import Any

from gramps.gen.datehandler import get_date as get_gramps_date
from gramps.gen.display.place import displayer as place_displayer

from genehelp.extractors.common import attribute_texts, bullet_texts, note_texts
from genehelp.l10n import _


@dataclass(frozen=True)
class EventDetails:
    """Normalized event fields shared by event, person, and family extractors."""

    event_type: str
    date: str
    description: str
    place: str
    notes: list[str]
    attributes: list[str]


def event_details(db: Any, event: Any) -> EventDetails:
    """Event details."""
    return EventDetails(
        event_type=event_type_text(event),
        date=get_gramps_date(event).strip(),
        description=(event.get_description() or "").strip(),
        place=event_place_text(db, event),
        notes=note_texts(db, event.get_note_list()),
        attributes=attribute_texts(event),
    )


def event_type_text(event: Any) -> str:
    """Event type text."""
    return str(event.get_type()).strip()


def event_place_text(db: Any, event: Any) -> str:
    """Event place text."""
    place_handle = event.get_place_handle()
    if not place_handle:
        return ""
    place = db.get_place_from_handle(place_handle)
    if place is None:
        return ""
    return (place_displayer.display(db, place) or "").strip()


def event_detail_lines(details: EventDetails) -> list[str]:
    """Event detail lines."""
    lines = []
    if details.event_type:
        lines.append(_("Event type: %s") % details.event_type)
    if details.date:
        lines.append(_("Date: %s") % details.date)
    if details.description:
        lines.append(_("Description: %s") % details.description)
    if details.place:
        lines.append(_("Place: %s") % details.place)

    if details.notes:
        lines.append(_("Notes:"))
        lines.extend(bullet_texts(details.notes))

    if details.attributes:
        lines.append(_("Event attributes:"))
        lines.extend(f"- {item}" for item in details.attributes)

    return lines


def event_list_item_lines(details: EventDetails) -> list[str]:
    """Event list item lines."""
    lines = []
    if details.event_type:
        lines.append("- " + (_("Event type: %s") % details.event_type))

    for label, value in [
        (_("Date"), details.date),
        (_("Description"), details.description),
        (_("Place"), details.place),
    ]:
        if value:
            lines.append(f"  {label}: {value}")

    if details.notes:
        lines.append("  " + _("Notes:"))
        lines.extend(bullet_texts(details.notes, prefix="  "))

    if details.attributes:
        lines.append("  " + _("Event attributes:"))
        lines.extend(f"  - {item}" for item in details.attributes)

    return lines


def event_life_text(details: EventDetails) -> str:
    """Event life text."""
    return ", ".join(
        value
        for value in [
            details.date,
            details.place,
            details.description,
        ]
        if value
    )
