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

"""Gramps object test doubles used by extractor tests."""

from typing import Any


class FakeCitationDb:
    """Test double that serves Gramps-like objects by handle."""

    def __init__(self, notes) -> None:
        """Initialize the test double."""
        self.notes = notes
        self.sources: dict[str, Any] = {}
        self.repositories: dict[str, Any] = {}
        self.places: dict[str, Any] = {}
        self.events: dict[str, Any] = {}
        self.people: dict[str, Any] = {}
        self.families: dict[str, Any] = {}
        self.backlinks: dict[str, list[tuple[str, str]]] = {}

    def get_note_from_handle(self, handle):
        """Return note from handle."""
        return self.notes.get(handle)

    def get_source_from_handle(self, handle):
        """Return source from handle."""
        return self.sources.get(handle)

    def get_repository_from_handle(self, handle):
        """Return repository from handle."""
        return self.repositories.get(handle)

    def get_place_from_handle(self, handle):
        """Return place from handle."""
        return self.places.get(handle)

    def get_event_from_handle(self, handle):
        """Return event from handle."""
        return self.events.get(handle)

    def get_person_from_handle(self, handle):
        """Return person from handle."""
        return self.people.get(handle)

    def get_family_from_handle(self, handle):
        """Return family from handle."""
        return self.families.get(handle)

    def find_backlink_handles(self, handle):
        """Find backlink handles."""
        return self.backlinks.get(handle, [])


class FakeNote:
    """Test double for a Gramps note object."""

    def __init__(self, text: str) -> None:
        """Initialize the test double."""
        self.text = text

    def get(self) -> str:
        """Get."""
        return self.text


class FakeAttribute:
    """Test double for a Gramps attribute object."""

    def __init__(self, attr_type: Any, value: str) -> None:
        """Initialize the test double."""
        self.attr_type = attr_type
        self.value = value

    def get_type(self) -> Any:
        """Return type."""
        return self.attr_type

    def get_value(self) -> str:
        """Return value."""
        return self.value


class FakeCitation:
    """Test double for a Gramps citation object."""

    def __init__(self, source_handle, page, note_handles, attributes) -> None:
        """Initialize the test double."""
        self.source_handle = source_handle
        self.page = page
        self.note_handles = note_handles
        self.attributes = attributes

    def get_reference_handle(self):
        """Return reference handle."""
        return self.source_handle

    def get_page(self):
        """Return page."""
        return self.page

    def get_note_list(self):
        """Return note list."""
        return self.note_handles

    def get_attribute_list(self):
        """Return attribute list."""
        return self.attributes


class FakeSource:
    """Test double for a Gramps source object."""

    def __init__(
        self,
        title,
        author,
        note_handles,
        attributes,
        publication_info="",
        abbreviation="",
        repo_refs=None,
    ) -> None:
        """Initialize the test double."""
        self.title = title
        self.author = author
        self.note_handles = note_handles
        self.attributes = attributes
        self.publication_info = publication_info
        self.abbreviation = abbreviation
        self.repo_refs = repo_refs or []

    def get_title(self):
        """Return title."""
        return self.title

    def get_author(self):
        """Return author."""
        return self.author

    def get_publication_info(self):
        """Return publication info."""
        return self.publication_info

    def get_abbreviation(self):
        """Return abbreviation."""
        return self.abbreviation

    def get_note_list(self):
        """Return note list."""
        return self.note_handles

    def get_attribute_list(self):
        """Return attribute list."""
        return self.attributes

    def get_reporef_list(self):
        """Return reporef list."""
        return self.repo_refs


class FakeRepoRef:
    """Test double for a Gramps repository reference."""

    def __init__(self, handle: str) -> None:
        """Initialize the test double."""
        self.handle = handle

    def get_reference_handle(self) -> str:
        """Return reference handle."""
        return self.handle


class FakeRepository:
    """Test double for a Gramps repository object."""

    def __init__(
        self,
        name: str,
        repo_type: str = "",
        urls=None,
        note_handles=None,
    ) -> None:
        """Initialize the test double."""
        self.name = name
        self.repo_type = repo_type
        self.urls = urls or []
        self.note_handles = note_handles or []

    def get_name(self) -> str:
        """Return name."""
        return self.name

    def get_type(self) -> str:
        """Return type."""
        return self.repo_type

    def get_url_list(self):
        """Return url list."""
        return self.urls

    def get_note_list(self):
        """Return note list."""
        return self.note_handles


class FakeRepositoryUrl:
    """Test double for a Gramps repository URL object."""

    def __init__(self, url_type: str, description: str, full_path: str) -> None:
        """Initialize the test double."""
        self.url_type = url_type
        self.description = description
        self.full_path = full_path

    def get_type(self) -> str:
        """Return type."""
        return self.url_type

    def get_description(self) -> str:
        """Return description."""
        return self.description

    def get_full_path(self) -> str:
        """Return full path."""
        return self.full_path


class FakeMedia:
    """Test double for a Gramps media object."""

    def __init__(
        self,
        path: str,
        note_handles=None,
        attributes=None,
    ) -> None:
        """Initialize the test double."""
        self.path = path
        self.note_handles = note_handles or []
        self.attributes = attributes or []

    def get_path(self) -> str:
        """Return path."""
        return self.path

    def get_note_list(self):
        """Return note list."""
        return self.note_handles

    def get_attribute_list(self):
        """Return attribute list."""
        return self.attributes


class FakePlace:
    """Test double for a Gramps place object."""

    def __init__(
        self,
        primary_name: str,
        alternative_names: list[str],
        latitude: str,
        longitude: str,
        note_handles: list[str],
    ) -> None:
        """Initialize the test double."""
        self.primary_name = FakePlaceName(primary_name)
        self.alternative_names = [FakePlaceName(name) for name in alternative_names]
        self.latitude = latitude
        self.longitude = longitude
        self.note_handles = note_handles

    def get_name(self):
        """Return name."""
        return self.primary_name

    def get_alternative_names(self):
        """Return alternative names."""
        return self.alternative_names

    def get_latitude(self) -> str:
        """Return latitude."""
        return self.latitude

    def get_longitude(self) -> str:
        """Return longitude."""
        return self.longitude

    def get_note_list(self):
        """Return note list."""
        return self.note_handles


class FakePlaceName:
    """Test double for a Gramps place name object."""

    def __init__(self, value: str) -> None:
        """Initialize the test double."""
        self.value = value

    def get_value(self) -> str:
        """Return value."""
        return self.value


class FakeEvent:
    """Test double for a Gramps event object."""

    def __init__(
        self,
        handle: str,
        event_type: str,
        date: str,
        description: str,
        place_handle: str,
        note_handles: list[str],
        attributes: list[FakeAttribute],
    ) -> None:
        """Initialize the test double."""
        self.handle = handle
        self.event_type = event_type
        self.date = date
        self.description = description
        self.place_handle = place_handle
        self.note_handles = note_handles
        self.attributes = attributes

    def get_type(self) -> str:
        """Return type."""
        return self.event_type

    def get_description(self) -> str:
        """Return description."""
        return self.description

    def get_place_handle(self) -> str:
        """Return place handle."""
        return self.place_handle

    def get_note_list(self):
        """Return note list."""
        return self.note_handles

    def get_attribute_list(self):
        """Return attribute list."""
        return self.attributes


class FakePerson:
    """Test double for a Gramps person object."""

    def __init__(
        self,
        name: str,
        gramps_id: str = "",
        gender: int = 2,
        birth_ref=None,
        death_ref=None,
        event_refs=None,
        family_handles=None,
        note_handles=None,
        attributes=None,
        surnames=None,
    ) -> None:
        """Initialize the test double."""
        self.name = name
        self.gramps_id = gramps_id
        self.gender = gender
        self.birth_ref = birth_ref
        self.death_ref = death_ref
        self.event_refs = event_refs or []
        self.family_handles = family_handles or []
        self.note_handles = note_handles or []
        self.attributes = attributes or []
        self.primary_name = FakePrimaryName(surnames or [])

    def get_gramps_id(self) -> str:
        """Return gramps id."""
        return self.gramps_id

    def get_gender(self) -> int:
        """Return gender."""
        return self.gender

    def get_birth_ref(self):
        """Return birth ref."""
        return self.birth_ref

    def get_death_ref(self):
        """Return death ref."""
        return self.death_ref

    def get_primary_name(self):
        """Return primary name."""
        return self.primary_name

    def get_event_ref_list(self):
        """Return event ref list."""
        return self.event_refs

    def get_family_handle_list(self):
        """Return family handle list."""
        return self.family_handles

    def get_note_list(self):
        """Return note list."""
        return self.note_handles

    def get_attribute_list(self):
        """Return attribute list."""
        return self.attributes


class FakePrimaryName:
    """Test double for a Gramps primary name object."""

    def __init__(self, surnames) -> None:
        """Initialize the test double."""
        self.surnames = surnames

    def get_surname_list(self):
        """Return surname list."""
        return self.surnames


class FakeSurname:
    """Test double for a Gramps surname object."""

    def __init__(self, surname: str, primary: bool = False) -> None:
        """Initialize the test double."""
        self.surname = surname
        self.primary = primary

    def get_surname(self) -> str:
        """Return surname."""
        return self.surname

    def get_primary(self) -> bool:
        """Return primary."""
        return self.primary


class FakeFamily:
    """Test double for a Gramps family object."""

    def __init__(
        self,
        father_handle: str,
        mother_handle: str,
        child_refs=None,
        event_refs=None,
        note_handles=None,
        attributes=None,
    ) -> None:
        """Initialize the test double."""
        self.father_handle = father_handle
        self.mother_handle = mother_handle
        self.child_refs = child_refs or []
        self.event_refs = event_refs or []
        self.note_handles = note_handles or []
        self.attributes = attributes or []

    def get_father_handle(self) -> str:
        """Return father handle."""
        return self.father_handle

    def get_mother_handle(self) -> str:
        """Return mother handle."""
        return self.mother_handle

    def get_child_ref_list(self):
        """Return child ref list."""
        return self.child_refs

    def get_event_ref_list(self):
        """Return event ref list."""
        return self.event_refs

    def get_note_list(self):
        """Return note list."""
        return self.note_handles

    def get_attribute_list(self):
        """Return attribute list."""
        return self.attributes


class FakeRef:
    """Test double for a Gramps handle reference."""

    def __init__(self, handle: str) -> None:
        """Initialize the test double."""
        self.ref = handle

    def get_reference_handle(self) -> str:
        """Return reference handle."""
        return self.ref
