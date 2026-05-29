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

"""Event extraction for GeneHelp request drafts."""

from typing import Any

from genehelp.config import DATA_SOURCE_EVENT
from genehelp.extractors.common import compact_description
from genehelp.extractors.gramps_events import event_detail_lines, event_details, event_type_text
from genehelp.extractors.gramps_people import person_display_name
from genehelp.l10n import _
from genehelp.models import ImportedContext


def extract_event(db: Any, event: Any, handle: str) -> ImportedContext:
    """Extract event."""
    event_type = event_type_text(event)
    people = event_people_text(db, event)
    return ImportedContext(
        nav_type=DATA_SOURCE_EVENT,
        handle=handle,
        description=build_event_text(db, event, event_type),
        title_values={
            "event_type": event_type or _("event"),
            "people": people or _("selected people"),
        },
    )


def build_event_text(db: Any, event: Any, _event_type: str) -> str:
    """Build event text."""
    return compact_description([event_detail_lines(event_details(db, event))])


def event_people_text(db: Any, event: Any) -> str:
    """Event people text."""
    names = []
    seen = set()
    for class_name, handle in db.find_backlink_handles(event.handle):
        for person_handle in person_handles_for_event_backlink(db, class_name, handle):
            if person_handle in seen:
                continue
            seen.add(person_handle)
            person = db.get_person_from_handle(person_handle)
            if person is None:
                continue
            name = person_display_name(person)
            if name:
                names.append(name)
    return ", ".join(names)


def person_handles_for_event_backlink(db: Any, class_name: str, handle: str) -> list[str]:
    """Person handles for event backlink."""
    if class_name == "Person":
        return [handle]
    if class_name != "Family":
        return []

    family = db.get_family_from_handle(handle)
    if family is None:
        return []
    return [
        person_handle
        for person_handle in [
            family.get_father_handle(),
            family.get_mother_handle(),
        ]
        if person_handle
    ]
