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

"""Unit tests for family and person extractors."""

from genehelp.extractors import family as family_extractor
from genehelp.extractors import gramps_events as gramps_event_helpers
from genehelp.extractors import gramps_people as gramps_people_helpers
from genehelp.extractors import person as person_extractor
from tests.fakes import (
    FakeAttribute,
    FakeCitationDb,
    FakeEvent,
    FakeFamily,
    FakeNote,
    FakePerson,
    FakeRef,
    FakeRepository,
    FakeSurname,
)
from tests.test_api_logic import expected_description


def test_family_description_includes_events_people_children_notes_and_attributes(
    monkeypatch,
) -> None:
    """Verify family description includes events people children notes and attributes."""
    monkeypatch.setattr(gramps_event_helpers, "get_gramps_date", lambda event: event.date)
    monkeypatch.setattr(
        gramps_event_helpers.place_displayer,
        "display",
        lambda _db, _place: "Poltava, Poltava Oblast, Ukraine",
    )
    monkeypatch.setattr(
        gramps_people_helpers.name_displayer,
        "display",
        lambda person: person.name,
    )

    db = FakeCitationDb(
        {
            "event-note": FakeNote("Marriage note text"),
            "family-note": FakeNote("Family note text"),
        }
    )
    db.places["place-1"] = FakeRepository("Poltava")
    db.events["marriage-event"] = FakeEvent(
        handle="marriage-event",
        event_type="Marriage",
        date="12 May 1897",
        description="Church wedding",
        place_handle="place-1",
        note_handles=["event-note"],
        attributes=[FakeAttribute("Witness", "Petro Ivanenko")],
    )
    db.events["father-birth"] = FakeEvent(
        handle="father-birth",
        event_type="Birth",
        date="1870",
        description="",
        place_handle="place-1",
        note_handles=[],
        attributes=[],
    )
    db.events["mother-death"] = FakeEvent(
        handle="mother-death",
        event_type="Death",
        date="1942",
        description="",
        place_handle="place-1",
        note_handles=[],
        attributes=[],
    )
    db.people["father"] = FakePerson(
        "Ivan Petrenko",
        gramps_id="I0001",
        gender=1,
        birth_ref=FakeRef("father-birth"),
        surnames=[FakeSurname("Petrenko", primary=True)],
    )
    db.people["mother"] = FakePerson(
        "Maria Kovalenko",
        gramps_id="I0002",
        gender=0,
        death_ref=FakeRef("mother-death"),
        surnames=[FakeSurname("Kovalenko", primary=True)],
    )
    db.people["child"] = FakePerson(
        "Petro Petrenko",
        gramps_id="I0003",
        gender=2,
        surnames=[FakeSurname("Petrenko", primary=True)],
    )
    family = FakeFamily(
        father_handle="father",
        mother_handle="mother",
        child_refs=[FakeRef("child")],
        event_refs=[FakeRef("marriage-event")],
        note_handles=["family-note"],
        attributes=[FakeAttribute("Research status", "Needs documents")],
    )

    context = family_extractor.extract_family(db, family, "family-1")

    assert context.nav_type == "Family"
    assert context.title_values == {
        "husband": "Ivan Petrenko",
        "wife": "Maria Kovalenko",
        "surname": "Petrenko",
    }
    assert context.description == expected_description(
        [
            "Family events:",
            "- Event type: Marriage",
            "  Date: 12 May 1897",
            "  Description: Church wedding",
            "  Place: Poltava, Poltava Oblast, Ukraine",
            "  Notes:",
            "  - Marriage note text",
            "  Event attributes:",
            "  - Witness: Petro Ivanenko",
        ],
        [
            "Husband:",
            "Name: Ivan Petrenko",
            "Gramps ID: I0001",
            "Gender: Male",
            "Birth: 1870, Poltava, Poltava Oblast, Ukraine",
        ],
        [
            "Wife:",
            "Name: Maria Kovalenko",
            "Gramps ID: I0002",
            "Gender: Female",
            "Death: 1942, Poltava, Poltava Oblast, Ukraine",
        ],
        [
            "Children:",
            "- Name: Petro Petrenko",
            "  Gramps ID: I0003",
            "  Gender: Unknown",
        ],
        [
            "Family notes:",
            "- Family note text",
        ],
        [
            "Family attributes:",
            "- Research status: Needs documents",
        ],
    )


def test_family_description_handles_missing_members_and_events() -> None:
    """Verify family extraction tolerates missing related objects."""
    db = FakeCitationDb({})
    family = FakeFamily(
        father_handle="missing-father",
        mother_handle="",
        child_refs=[FakeRef("missing-child")],
        event_refs=[FakeRef("missing-event")],
    )

    context = family_extractor.extract_family(db, family, "family-1")

    assert context.title_values == {
        "husband": "husband",
        "wife": "wife",
        "surname": "family",
    }
    assert context.description == expected_description(
        [
            "Husband:",
            "Not specified",
        ],
        [
            "Wife:",
            "Not specified",
        ],
    )


def test_person_description_includes_events_partner_notes_and_attributes(
    monkeypatch,
) -> None:
    """Verify person description includes events partner notes and attributes."""
    monkeypatch.setattr(gramps_event_helpers, "get_gramps_date", lambda event: event.date)
    monkeypatch.setattr(
        gramps_event_helpers.place_displayer,
        "display",
        lambda _db, _place: "Poltava, Poltava Oblast, Ukraine",
    )
    monkeypatch.setattr(
        gramps_people_helpers.name_displayer,
        "display",
        lambda person: person.name,
    )

    db = FakeCitationDb(
        {
            "event-note": FakeNote("Moved from another town"),
            "person-note": FakeNote("Person note text"),
        }
    )
    db.places["place-1"] = FakeRepository("Poltava")
    db.events["birth-event"] = FakeEvent(
        handle="birth-event",
        event_type="Birth",
        date="1870",
        description="",
        place_handle="place-1",
        note_handles=[],
        attributes=[],
    )
    db.events["origin-event"] = FakeEvent(
        handle="origin-event",
        event_type="Residence",
        date="1890",
        description="Arrived in Poltava",
        place_handle="place-1",
        note_handles=["event-note"],
        attributes=[FakeAttribute("Source clue", "Household list")],
    )
    db.people["person"] = FakePerson(
        "Ivan Petrenko",
        gramps_id="I0001",
        gender=1,
        birth_ref=FakeRef("birth-event"),
        event_refs=[FakeRef("birth-event"), FakeRef("origin-event")],
        family_handles=["family-1"],
        note_handles=["person-note"],
        attributes=[FakeAttribute("Occupation", "Blacksmith")],
        surnames=[FakeSurname("Petrenko", primary=True)],
    )
    db.people["partner"] = FakePerson(
        "Maria Kovalenko",
        gramps_id="I0002",
        gender=0,
        surnames=[FakeSurname("Kovalenko", primary=True)],
    )
    db.families["family-1"] = FakeFamily("person", "partner")

    context = person_extractor.extract_person(db, db.people["person"], "person")

    assert context.nav_type == "Person"
    assert context.title_values == {"person": "Ivan Petrenko"}
    assert context.description == expected_description(
        [
            "Person:",
            "Name: Ivan Petrenko",
            "Gramps ID: I0001",
            "Gender: Male",
            "Birth: 1870, Poltava, Poltava Oblast, Ukraine",
        ],
        [
            "Person events:",
            "- Event type: Birth",
            "  Date: 1870",
            "  Place: Poltava, Poltava Oblast, Ukraine",
            "- Event type: Residence",
            "  Date: 1890",
            "  Description: Arrived in Poltava",
            "  Place: Poltava, Poltava Oblast, Ukraine",
            "  Notes:",
            "  - Moved from another town",
            "  Event attributes:",
            "  - Source clue: Household list",
        ],
        [
            "Partners:",
            "- Name: Maria Kovalenko",
            "  Gramps ID: I0002",
            "  Gender: Female",
        ],
        [
            "Person attributes:",
            "- Occupation: Blacksmith",
        ],
        [
            "Person notes:",
            "- Person note text",
        ],
    )


def test_person_description_deduplicates_partners_and_skips_missing_handles(
    monkeypatch,
) -> None:
    """Verify person partner extraction skips duplicates and missing family members."""
    monkeypatch.setattr(
        gramps_people_helpers.name_displayer,
        "display",
        lambda person: person.name,
    )
    db = FakeCitationDb({})
    db.people["person"] = FakePerson(
        "Ivan Petrenko",
        family_handles=["family-1", "family-2", "missing-family"],
    )
    db.people["partner"] = FakePerson("Maria Kovalenko")
    db.families["family-1"] = FakeFamily("person", "partner")
    db.families["family-2"] = FakeFamily("person", "partner")

    partners = person_extractor.person_partners(db, db.people["person"], "person")
    context = person_extractor.extract_person(db, db.people["person"], "person")

    assert partners == [db.people["partner"]]
    assert "Partners:\n- Name: Maria Kovalenko" in context.description
