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

"""Shared Gramps person formatting helpers."""

from typing import Any

from gramps.gen.display.name import displayer as name_displayer

from genehelp.extractors.common import reference_handle
from genehelp.extractors.gramps_events import event_details, event_life_text
from genehelp.l10n import _


def person_for_handle(db: Any, handle: str) -> Any:
    """Person for handle."""
    if not handle:
        return None
    return db.get_person_from_handle(handle)


def person_display_name(person: Any) -> str:
    """Person display name."""
    if person is None:
        return ""
    return (name_displayer.display(person) or "").strip()


def person_basic_lines(db: Any, person: Any) -> list[str]:
    """Person basic lines."""
    if person is None:
        return [_("Not specified")]

    lines = []
    name = person_display_name(person)
    if name:
        lines.append(_("Name: %s") % name)

    gramps_id = person_gramps_id(person)
    if gramps_id:
        lines.append(_("Gramps ID: %s") % gramps_id)

    gender = person_gender_label(person)
    if gender:
        lines.append(_("Gender: %s") % gender)

    birth = person_life_event_text(db, person, "get_birth_ref")
    if birth:
        lines.append(_("Birth: %s") % birth)

    death = person_life_event_text(db, person, "get_death_ref")
    if death:
        lines.append(_("Death: %s") % death)

    return lines or [_("No basic person data found")]


def person_gramps_id(person: Any) -> str:
    """Person gramps id."""
    get_gramps_id = getattr(person, "get_gramps_id", None)
    if get_gramps_id is None:
        return ""
    return (get_gramps_id() or "").strip()


def person_gender_label(person: Any) -> str:
    """Person gender label."""
    get_gender = getattr(person, "get_gender", None)
    if get_gender is None:
        return ""
    gender = get_gender()
    labels = {
        1: _("Male"),
        0: _("Female"),
        3: _("Other"),
        2: _("Unknown"),
    }
    return labels.get(gender, _("Unknown"))


def person_life_event_text(db: Any, person: Any, ref_getter_name: str) -> str:
    """Person life event text."""
    ref_getter = getattr(person, ref_getter_name, None)
    if ref_getter is None:
        return ""
    event_ref = ref_getter()
    event_handle = reference_handle(event_ref)
    if not event_handle:
        return ""
    event = db.get_event_from_handle(event_handle)
    if event is None:
        return ""
    return event_life_text(event_details(db, event))


def family_surname(husband: Any, wife: Any) -> str:
    """Family surname."""
    for person in [husband, wife]:
        surname = person_primary_surname(person)
        if surname:
            return surname
    return ""


def person_primary_surname(person: Any) -> str:
    """Person primary surname."""
    if person is None:
        return ""
    primary_name = person.get_primary_name()
    if primary_name is None:
        return ""
    surnames = primary_name.get_surname_list()
    for surname in surnames:
        value = (surname.get_surname() or "").strip()
        if value and surname.get_primary():
            return value
    for surname in surnames:
        value = (surname.get_surname() or "").strip()
        if value:
            return value
    return ""
