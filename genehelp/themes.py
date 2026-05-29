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

"""Request topic templates for supported Gramps page types."""

from genehelp.config import (
    DATA_SOURCE_CITATION,
    DATA_SOURCE_EVENT,
    DATA_SOURCE_FAMILY,
    DATA_SOURCE_MEDIA,
    DATA_SOURCE_NOTE,
    DATA_SOURCE_PERSON,
    DATA_SOURCE_PLACE,
    DATA_SOURCE_REPOSITORY,
    DATA_SOURCE_SOURCE,
)
from genehelp.extractors import (
    extract_citation,
    extract_event,
    extract_family,
    extract_media,
    extract_note,
    extract_person,
    extract_place,
    extract_repository,
    extract_source,
)
from genehelp.l10n import _
from genehelp.models import PageHandler, ThemeOption

MEDIA_THEMES = (
    ThemeOption(
        key="identify_photo",
        api_theme="identify_photo",
        label=_("Help identify who is in the photo"),
        default_title=_("Help identify who is in the photo"),
        button_id="media_theme_identify_photo_radio",
    ),
    ThemeOption(
        key="identify_map_location",
        api_theme="identify_map_location",
        label=_("What place is shown on this map? Help identify the exact coordinates"),
        default_title=_("What place is shown on this map? Help identify the exact coordinates"),
        button_id="media_theme_identify_map_location_radio",
    ),
    ThemeOption(
        key="identify_seal",
        api_theme="identify_photo",
        label=_("Looking for a specialist to identify this seal"),
        default_title=_("Looking for a specialist to identify this seal"),
        button_id="media_theme_identify_seal_radio",
    ),
    ThemeOption(
        key="identify_coat_of_arms",
        api_theme="identify_photo",
        label=_("Find out which family or institution this coat of arms belonged to"),
        default_title=_("Find out which family or institution this coat of arms belonged to"),
        button_id="media_theme_identify_coat_of_arms_radio",
    ),
)

NOTE_THEMES = (
    ThemeOption(
        key="note_verify_assumption",
        api_theme="identify_photo",
        label=_("Help verify this assumption"),
        default_title=_("Help verify this assumption"),
        button_id="note_theme_verify_assumption_radio",
    ),
    ThemeOption(
        key="note_genealogy_blocker",
        api_theme="identify_photo",
        label=_("I'm stuck. Help me move past a genealogy roadblock"),
        default_title=_("I'm stuck. Help me move past a genealogy roadblock"),
        button_id="note_theme_genealogy_blocker_radio",
    ),
    ThemeOption(
        key="note_family_legend",
        api_theme="identify_photo",
        label=_("Looking for records that confirm or disprove a family legend"),
        default_title=_("Looking for records that confirm or disprove a family legend"),
        button_id="note_theme_family_legend_radio",
    ),
)

REPOSITORY_THEMES = (
    ThemeOption(
        key="repository_archive_physical_presence",
        api_theme="repository_archive_help",
        label=_("A local researcher needs to visit the archive in person"),
        default_title=_("A local researcher needs to visit the archive in person: {name}"),
        button_id="repository_theme_physical_presence_radio",
    ),
    ThemeOption(
        key="repository_archive_digitization",
        api_theme="repository_archive_help",
        label=_("A local researcher needs to request archive file digitization"),
        default_title=_("A local researcher needs to request archive file digitization: {name}"),
        button_id="repository_theme_digitization_radio",
    ),
)

CITATION_THEMES = (
    ThemeOption(
        key="citation_find_original_document",
        api_theme="identify_photo",
        label=_("Find the original document that confirms this citation"),
        default_title=_("Find the original document that confirms this citation"),
        button_id="citation_theme_find_original_document_radio",
    ),
    ThemeOption(
        key="citation_online_consultation",
        api_theme="identify_photo",
        label=_("Need an expert for an online consultation"),
        default_title=_("Need an expert for an online consultation"),
        button_id="citation_theme_online_consultation_radio",
    ),
)

SOURCE_THEMES = (
    ThemeOption(
        key="source_archive_digitization",
        api_theme="repository_archive_help",
        label=_("Looking for a local researcher who can digitize an archival file"),
        default_title=_("Looking for a local researcher who can digitize an archival file"),
        button_id="source_theme_archive_digitization_radio",
    ),
    ThemeOption(
        key="source_cemetery_headstone",
        api_theme="repository_archive_help",
        label=_("Need someone who can visit the cemetery and find the grave marker"),
        default_title=_("Need someone who can visit the cemetery and find the grave marker"),
        button_id="source_theme_cemetery_headstone_radio",
    ),
)

PLACE_THEMES = (
    ThemeOption(
        key="place_find_records",
        api_theme="repository_archive_help",
        label=_("Find where to look for records for {name}"),
        default_title=_("Find where to look for records for {name}"),
        button_id="place_theme_find_records_radio",
    ),
    ThemeOption(
        key="place_prepare_file_list",
        api_theme="repository_archive_help",
        label=_("Help prepare a list of archival files for researching {name}"),
        default_title=_("Help prepare a list of archival files for researching {name}"),
        button_id="place_theme_prepare_file_list_radio",
    ),
)

EVENT_THEMES = (
    ThemeOption(
        key="event_find_document",
        api_theme="identify_photo",
        label=_("Find a document about the {event_type} event for {people}"),
        default_title=_("Find a document about the {event_type} event for {people}"),
        button_id="event_theme_find_document_radio",
    ),
    ThemeOption(
        key="event_verify_date_or_place",
        api_theme="identify_photo",
        label=_("Verify the date or place of the event"),
        default_title=_("Verify the date or place of the event"),
        button_id="event_theme_verify_date_or_place_radio",
    ),
)

FAMILY_THEMES = (
    ThemeOption(
        key="family_find_marriage_record",
        api_theme="identify_photo",
        label=_("Find a marriage record for the family of {husband} and {wife}"),
        default_title=_("Find a marriage record for the family of {husband} and {wife}"),
        button_id="family_theme_find_marriage_record_radio",
    ),
    ThemeOption(
        key="family_confirm_children",
        api_theme="identify_photo",
        label=_("Help confirm the children in the {surname} family; records are missing"),
        default_title=_("Help confirm the children in the {surname} family; records are missing"),
        button_id="family_theme_confirm_children_radio",
    ),
)

PERSON_THEMES = (
    ThemeOption(
        key="person_find_birth_record",
        api_theme="identify_photo",
        label=_("Find birth record for {person}"),
        default_title=_("Find birth record for {person}"),
        button_id="person_theme_find_birth_record_radio",
    ),
    ThemeOption(
        key="person_find_death_record",
        api_theme="identify_photo",
        label=_("Find death record for {person}"),
        default_title=_("Find death record for {person}"),
        button_id="person_theme_find_death_record_radio",
    ),
    ThemeOption(
        key="person_origin_blocker",
        api_theme="identify_photo",
        label=_("Cannot find where {person} came from"),
        default_title=_("Cannot find where {person} came from"),
        button_id="person_theme_origin_blocker_radio",
    ),
)

PAGE_HANDLERS = {
    DATA_SOURCE_MEDIA: PageHandler(
        nav_type=DATA_SOURCE_MEDIA,
        object_getter_name="get_media_from_handle",
        theme_box_id="media_theme_box",
        theme_section_label_id="media_theme_section_label",
        themes=MEDIA_THEMES,
        extractor=extract_media,
    ),
    DATA_SOURCE_NOTE: PageHandler(
        nav_type=DATA_SOURCE_NOTE,
        object_getter_name="get_note_from_handle",
        theme_box_id="note_theme_box",
        theme_section_label_id="note_theme_section_label",
        themes=NOTE_THEMES,
        extractor=extract_note,
    ),
    DATA_SOURCE_REPOSITORY: PageHandler(
        nav_type=DATA_SOURCE_REPOSITORY,
        object_getter_name="get_repository_from_handle",
        theme_box_id="repository_theme_box",
        theme_section_label_id="repository_theme_section_label",
        themes=REPOSITORY_THEMES,
        extractor=extract_repository,
    ),
    DATA_SOURCE_CITATION: PageHandler(
        nav_type=DATA_SOURCE_CITATION,
        object_getter_name="get_citation_from_handle",
        theme_box_id="citation_theme_box",
        theme_section_label_id="citation_theme_section_label",
        themes=CITATION_THEMES,
        extractor=extract_citation,
    ),
    DATA_SOURCE_SOURCE: PageHandler(
        nav_type=DATA_SOURCE_SOURCE,
        object_getter_name="get_source_from_handle",
        theme_box_id="source_theme_box",
        theme_section_label_id="source_theme_section_label",
        themes=SOURCE_THEMES,
        extractor=extract_source,
    ),
    DATA_SOURCE_PLACE: PageHandler(
        nav_type=DATA_SOURCE_PLACE,
        object_getter_name="get_place_from_handle",
        theme_box_id="place_theme_box",
        theme_section_label_id="place_theme_section_label",
        themes=PLACE_THEMES,
        extractor=extract_place,
    ),
    DATA_SOURCE_EVENT: PageHandler(
        nav_type=DATA_SOURCE_EVENT,
        object_getter_name="get_event_from_handle",
        theme_box_id="event_theme_box",
        theme_section_label_id="event_theme_section_label",
        themes=EVENT_THEMES,
        extractor=extract_event,
    ),
    DATA_SOURCE_FAMILY: PageHandler(
        nav_type=DATA_SOURCE_FAMILY,
        object_getter_name="get_family_from_handle",
        theme_box_id="family_theme_box",
        theme_section_label_id="family_theme_section_label",
        themes=FAMILY_THEMES,
        extractor=extract_family,
    ),
    DATA_SOURCE_PERSON: PageHandler(
        nav_type=DATA_SOURCE_PERSON,
        object_getter_name="get_person_from_handle",
        theme_box_id="person_theme_box",
        theme_section_label_id="person_theme_section_label",
        themes=PERSON_THEMES,
        extractor=extract_person,
    ),
}

SUPPORTED_NAV_TYPES = tuple(PAGE_HANDLERS.keys())


def theme_for_key(nav_type: str, theme_key: str) -> ThemeOption | None:
    """Theme for key."""
    handler = PAGE_HANDLERS.get(nav_type)
    if handler is None:
        return None

    for theme in handler.themes:
        if theme.key == theme_key:
            return theme
    return None
