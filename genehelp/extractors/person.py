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

"""Person extraction for GeneHelp request drafts."""

from typing import Any

from genehelp.config import DATA_SOURCE_PERSON
from genehelp.extractors.common import (
    attribute_texts,
    bullet_texts,
    compact_description,
    note_texts,
    prefixed_block_lines,
    reference_handle,
    titled_block,
)
from genehelp.extractors.gramps_events import event_details, event_list_item_lines
from genehelp.extractors.gramps_people import (
    person_basic_lines,
    person_display_name,
)
from genehelp.l10n import _
from genehelp.models import ImportedContext


def extract_person(db: Any, person: Any, handle: str) -> ImportedContext:
    """Extract person."""
    person_name = person_display_name(person)
    return ImportedContext(
        nav_type=DATA_SOURCE_PERSON,
        handle=handle,
        description=build_person_text(db, person, handle),
        title_values={"person": person_name or _("selected person")},
    )


def build_person_text(db: Any, person: Any, handle: str) -> str:
    """Build person text."""
    blocks = [
        titled_block(_("Person:"), person_basic_lines(db, person)),
        titled_block(_("Person events:"), person_event_lines(db, person)),
    ]

    partners = person_partners(db, person, handle)
    if partners:
        partner_lines = []
        for partner in partners:
            partner_lines.extend(prefixed_block_lines(person_basic_lines(db, partner)))
        blocks.append(titled_block(_("Partners:"), partner_lines))

    attributes = attribute_texts(person)
    blocks.append(titled_block(_("Person attributes:"), bullet_texts(attributes)))

    notes = note_texts(db, person.get_note_list())
    blocks.append(titled_block(_("Person notes:"), bullet_texts(notes)))

    return compact_description(blocks)


def person_event_lines(db: Any, person: Any) -> list[str]:
    """Person event lines."""
    lines = []
    for event_ref in person.get_event_ref_list():
        event_handle = reference_handle(event_ref)
        if not event_handle:
            continue
        event = db.get_event_from_handle(event_handle)
        if event is None:
            continue
        lines.extend(event_list_item_lines(event_details(db, event)))
    return lines


def person_partners(db: Any, person: Any, handle: str) -> list[Any]:
    """Person partners."""
    partners = []
    seen = set()
    for family_handle in person.get_family_handle_list():
        family = db.get_family_from_handle(family_handle)
        if family is None:
            continue
        for partner_handle in [family.get_father_handle(), family.get_mother_handle()]:
            if not partner_handle or partner_handle == handle or partner_handle in seen:
                continue
            partner = db.get_person_from_handle(partner_handle)
            if partner is None:
                continue
            seen.add(partner_handle)
            partners.append(partner)
    return partners
