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

"""Family extraction for GeneHelp request drafts."""

from typing import Any

from genehelp.config import DATA_SOURCE_FAMILY
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
    family_surname,
    person_basic_lines,
    person_display_name,
    person_for_handle,
)
from genehelp.l10n import _
from genehelp.models import ImportedContext


def extract_family(db: Any, family: Any, handle: str) -> ImportedContext:
    """Extract family."""
    husband = person_for_handle(db, family.get_father_handle())
    wife = person_for_handle(db, family.get_mother_handle())
    return ImportedContext(
        nav_type=DATA_SOURCE_FAMILY,
        handle=handle,
        description=build_family_text(db, family, husband, wife),
        title_values={
            "husband": person_display_name(husband) or _("husband"),
            "wife": person_display_name(wife) or _("wife"),
            "surname": family_surname(husband, wife) or _("family"),
        },
    )


def build_family_text(db: Any, family: Any, husband: Any, wife: Any) -> str:
    """Build family text."""
    blocks = [
        titled_block(_("Family events:"), family_event_lines(db, family)),
        titled_block(_("Husband:"), person_basic_lines(db, husband)),
        titled_block(_("Wife:"), person_basic_lines(db, wife)),
    ]

    children = family_children(db, family)
    if children:
        child_lines = []
        for child in children:
            child_lines.extend(prefixed_block_lines(person_basic_lines(db, child)))
        blocks.append(titled_block(_("Children:"), child_lines))

    notes = note_texts(db, family.get_note_list())
    blocks.append(titled_block(_("Family notes:"), bullet_texts(notes)))

    attributes = attribute_texts(family)
    blocks.append(titled_block(_("Family attributes:"), bullet_texts(attributes)))

    return compact_description(blocks)


def family_children(db: Any, family: Any) -> list[Any]:
    """Family children."""
    children = []
    for child_ref in family.get_child_ref_list():
        child_handle = reference_handle(child_ref)
        child = person_for_handle(db, child_handle)
        if child is not None:
            children.append(child)
    return children


def family_event_lines(db: Any, family: Any) -> list[str]:
    """Family event lines."""
    lines = []
    for event_ref in family.get_event_ref_list():
        event_handle = reference_handle(event_ref)
        if not event_handle:
            continue
        event = db.get_event_from_handle(event_handle)
        if event is None:
            continue

        lines.extend(event_list_item_lines(event_details(db, event)))
    return lines
