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

"""Unit tests for API parsing, payloads, and Gramps extractors."""

from genehelp.api_client import (
    ApiClient,
    absolute_url,
    multipart_body,
    parse_api_error,
    parse_retry_after_seconds,
)
from genehelp.api_contract import (
    COUNTRY_SOURCE_UNKNOWN,
    COUNTRY_SOURCE_USER_SELECTED,
    FIELD_DESCRIPTION,
    FIELD_HELPER_COUNTRY_CODE,
    FIELD_HELPER_COUNTRY_SOURCE,
    FIELD_IS_TEST,
    FIELD_REQUEST_COUNTRY_CODE,
    FIELD_REQUEST_COUNTRY_SOURCE,
    FIELD_THEME,
    FIELD_TITLE,
    API_BASE_URL,
)
from genehelp.countries import (
    FALLBACK_COUNTRY_LOCALE,
    parse_countries_response,
    parse_country_locales_response,
    select_country_locale,
)
from genehelp.config import normalize_api_base_url
from genehelp.country_utils import (
    country_display,
    country_match_sort_key,
    country_matches_query,
    normalize_country_code,
)
from genehelp.extractors.common import attribute_texts, bullet_texts, compact_description
from genehelp.extractors.common import reference_handle
from genehelp.extractors import citation as citation_extractor
from genehelp.extractors import event as event_extractor
from genehelp.extractors import gramps_events as gramps_event_helpers
from genehelp.extractors import gramps_people as gramps_people_helpers
from genehelp.extractors import media as media_extractor
from genehelp.extractors import note as note_extractor
from genehelp.extractors import place as place_extractor
from genehelp.extractors import repository as repository_extractor
from genehelp.extractors import source as source_extractor
from genehelp.help_offer import parse_help_offer_response
from genehelp.models import CountryOption, GenealogyRequestItem, ImportedContext, ThemeOption
from genehelp.payloads import build_submit_payload
from genehelp.genealogy_requests import parse_genealogy_requests_response
from genehelp.ui import format_template
from genehelp.ui_requests import display_datetime, request_item_status_badge, status_badge
from tests.fakes import (
    FakeAttribute,
    FakeCitation,
    FakeCitationDb,
    FakeEvent,
    FakeFamily,
    FakeMedia,
    FakeNote,
    FakePerson,
    FakePlace,
    FakeRef,
    FakeRepoRef,
    FakeRepository,
    FakeRepositoryUrl,
    FakeSource,
)


TEST_LOCAL_API_BASE_URL = "http://127.0.0.1:8007"


def expected_description(*blocks: list[str]) -> str:
    """Expected description."""
    return "\n\n".join("\n".join(block) for block in blocks if block)


def test_build_submit_payload_normalizes_country_fields() -> None:
    """Verify build submit payload normalizes country fields."""
    payload = build_submit_payload(
        ImportedContext(
            nav_type="Media",
            handle="M1",
            description="Imported text",
            file_path="/tmp/photo.jpg",
        ),
        ThemeOption(
            key="identify_photo",
            api_theme="identify_photo",
            label="Identify photo",
            default_title="Identify photo",
            button_id="theme_button",
        ),
        "  Title  ",
        "  Description  ",
        " ua ",
        "",
    )

    assert payload.file_path == "/tmp/photo.jpg"
    assert payload.fields[FIELD_THEME] == "identify_photo"
    assert payload.fields[FIELD_TITLE] == "Title"
    assert payload.fields[FIELD_DESCRIPTION] == "Description"
    assert payload.fields[FIELD_REQUEST_COUNTRY_CODE] == "UA"
    assert payload.fields[FIELD_REQUEST_COUNTRY_SOURCE] == COUNTRY_SOURCE_USER_SELECTED
    assert payload.fields[FIELD_HELPER_COUNTRY_CODE] == ""
    assert payload.fields[FIELD_HELPER_COUNTRY_SOURCE] == COUNTRY_SOURCE_UNKNOWN
    assert payload.fields[FIELD_IS_TEST] == "0"


def test_build_submit_payload_marks_test_requests() -> None:
    """Verify build submit payload marks test requests."""
    payload = build_submit_payload(
        ImportedContext(nav_type="Media", handle="M1", description="Imported text"),
        ThemeOption(
            key="identify_photo",
            api_theme="identify_photo",
            label="Identify photo",
            default_title="Identify photo",
            button_id="theme_button",
        ),
        "Title",
        "Description",
        "",
        "",
        is_test=True,
    )

    assert payload.fields[FIELD_IS_TEST] == "1"


def test_build_submit_payload_rejects_missing_required_fields() -> None:
    """Verify build submit payload rejects missing required fields."""
    theme = ThemeOption(
        key="identify_photo",
        api_theme="identify_photo",
        label="Identify photo",
        default_title="Identify photo",
        button_id="theme_button",
    )

    try:
        build_submit_payload(
            ImportedContext(nav_type="Media", handle="M1", description="Imported text"),
            theme,
            " ",
            "Description",
            "",
            "",
        )
    except ValueError as exc:
        assert str(exc) == "Missing submit payload fields."
    else:
        raise AssertionError("Expected ValueError for an empty title.")


def test_api_client_builds_urls_from_single_base_constant() -> None:
    """Verify api client builds urls from single base constant."""
    client = ApiClient("/api/example", "token")
    local_client = ApiClient("/api/example", "token", base_url=f"{TEST_LOCAL_API_BASE_URL}/")

    assert client.request_url() == f"{API_BASE_URL}/api/example"
    assert client.request_url({"locale": "en"}) == (f"{API_BASE_URL}/api/example?locale=en")
    assert absolute_url("/profile") == f"{API_BASE_URL}/profile"
    assert local_client.request_url() == f"{TEST_LOCAL_API_BASE_URL}/api/example"
    assert local_client.absolute_url("/profile") == f"{TEST_LOCAL_API_BASE_URL}/profile"
    assert absolute_url("https://example.test/profile") == "https://example.test/profile"


def test_api_base_url_config_uses_production_fallback() -> None:
    """Verify API base URL config defaults to production and accepts local override."""
    assert normalize_api_base_url("") == API_BASE_URL
    assert normalize_api_base_url(f"'{TEST_LOCAL_API_BASE_URL}/'") == TEST_LOCAL_API_BASE_URL
    assert normalize_api_base_url("not-a-url") == API_BASE_URL


def test_api_error_payload_parser_ignores_malformed_shapes() -> None:
    """Verify api error payload parser ignores malformed shapes."""
    assert parse_api_error('{"error":{"code":"token_invalid","message":"Invalid token"}}') == (
        "token_invalid",
        "Invalid token",
    )
    assert parse_api_error(
        '{"error":{"code":"validation_failed",'
        '"message":"The request data did not pass validation.",'
        '"status":422,"details":{"title":[{"code":"required","message":"Required."}]}}}'
    ) == (
        "validation_failed",
        "The request data did not pass validation.",
    )
    assert parse_api_error('{"message":"The title field is required.","errors":{}}') == (
        "",
        "The title field is required.",
    )
    assert parse_api_error('{"error":{"code":42,"message":false}}') == ("", "")
    assert parse_api_error("not json") == ("", "")


def test_retry_after_parser_accepts_delay_seconds_only() -> None:
    """Verify Retry-After parser reads delay seconds and ignores date-like values."""
    assert parse_retry_after_seconds("61") == 61
    assert parse_retry_after_seconds(" 5 ") == 5
    assert parse_retry_after_seconds("0") is None
    assert parse_retry_after_seconds("-1") is None
    assert parse_retry_after_seconds("Wed, 21 Oct 2015 07:28:00 GMT") is None
    assert parse_retry_after_seconds(None) is None


def test_multipart_body_includes_fields_and_optional_file(tmp_path) -> None:
    """Verify multipart body includes fields and optional file."""
    media_path = tmp_path / "document.jpg"
    media_path.write_bytes(b"JPEGDATA")

    body, content_type = multipart_body(
        {"title": "Archive request", "is_test": "1"},
        "media",
        str(media_path),
    )

    assert content_type.startswith("multipart/form-data; boundary=----Genehelp")
    assert b'name="title"\r\n\r\nArchive request' in body
    assert b'name="is_test"\r\n\r\n1' in body
    assert b'name="media"; filename="document.jpg"' in body
    assert b"Content-Type: image/jpeg" in body
    assert b"JPEGDATA" in body


def test_parse_country_data_normalizes_and_sorts_values() -> None:
    """Verify parse country data normalizes and sorts values."""
    countries = parse_countries_response(
        {
            "data": [
                {"code": "ua", "name": "Ukraine"},
                {"code": "pl", "name": " Poland "},
                {"code": "", "name": "Ignored"},
                "ignored",
            ]
        }
    )

    assert [country.code for country in countries] == ["PL", "UA"]
    assert [country.name for country in countries] == ["Poland", "Ukraine"]


def test_country_ui_helpers_match_codes_names_and_display_values() -> None:
    """Verify country ui helpers match codes names and display values."""
    country = CountryOption(code="UA", name="Ukraine")

    assert normalize_country_code(" ua ") == "UA"
    assert country_display(country) == "UA - Ukraine"
    assert country_matches_query(country, "ukr") is True
    assert country_matches_query(country, "ua") is True
    assert country_matches_query(country, "pl") is False
    assert country_match_sort_key(country, "ua")[0] == 0


def test_description_helpers_keep_groups_compact_and_notes_readable() -> None:
    """Verify description helpers keep groups compact and notes readable."""
    assert compact_description(
        [
            ["Title: Archive file", "Author: Archive"],
            ["Notes:", *bullet_texts(["First note\ncontinued", "Second note"])],
        ]
    ) == (
        "Title: Archive file\nAuthor: Archive\n\n"
        "Notes:\n- First note\n  continued\n- Second note"
    )


def test_parse_country_locales_deduplicates_and_uses_fallback() -> None:
    """Verify parse country locales deduplicates and uses fallback."""
    locales, fallback = parse_country_locales_response(
        {"locales": ["uk-UA", "uk", "en"], "fallback": "pl-PL"}
    )

    assert locales == ["uk", "en"]
    assert fallback == "pl"
    assert select_country_locale("uk", locales, fallback) == "uk"
    assert select_country_locale("de", locales, fallback) == "pl"
    assert select_country_locale("de", [], "") == FALLBACK_COUNTRY_LOCALE


def test_parse_help_offer_response_uses_typed_sections_and_nested_items() -> None:
    """Verify parse help offer response uses typed sections."""
    offer = parse_help_offer_response(
        {
            "data": {
                "user_id": 123,
                "profile_url": "/profile",
                "can_online": True,
                "can_offline": False,
                "helper_country_code": "UA",
                "helper_country_source": "user_selected",
                "sections": [
                    {
                        "key": "channels",
                        "label": "Help format",
                        "type": "channels",
                        "items": [
                            {
                                "key": "online",
                                "label": "Online",
                                "description": "Remote help",
                                "enabled": True,
                            },
                            {"key": "offline", "label": "Offline", "enabled": False},
                        ],
                    },
                    {
                        "key": "online_area",
                        "label": "Locations",
                        "type": "access_points",
                        "items": [
                            {
                                "location_type": "place",
                                "country_code": "ua",
                                "place_name": "Kyiv",
                                "radius_km": "25",
                            }
                        ],
                    },
                    {
                        "key": "historical_periods",
                        "label": "Periods",
                        "type": "enabled_values",
                        "items": [
                            {
                                "key": "russian_empire",
                                "selection_type": "context",
                                "label": "Russian Empire",
                                "enabled": True,
                                "from_year": "1721",
                                "to_year": "1917",
                            }
                        ],
                    },
                    {
                        "key": "document_types",
                        "label": "Documents",
                        "type": "enabled_values",
                        "items": [
                            {
                                "document_type_key": "metric_books",
                                "label": "Metric books",
                                "enabled": False,
                            }
                        ],
                    },
                ],
            }
        }
    )

    assert offer is not None
    assert offer.user_id == ""
    assert offer.profile_url == f"{API_BASE_URL}/profile"
    assert offer.helper_country_code == "UA"
    assert len(offer.sections) == 4
    assert offer.sections[0].items[0].key == "online"
    assert offer.sections[0].items[0].enabled is True
    assert offer.sections[1].items[0].place_name == "Kyiv"
    assert offer.sections[1].items[0].radius_km == 25
    assert offer.sections[2].items[0].from_year == 1721
    assert offer.sections[2].items[0].to_year == 1917
    assert offer.sections[3].items[0].key == "metric_books"
    assert offer.sections[3].items[0].enabled is False


def test_parse_genealogy_requests_filters_invalid_items_and_normalizes_urls() -> None:
    """Verify parse genealogy requests filters invalid items and normalizes urls."""
    groups = parse_genealogy_requests_response(
        {
            "data": [
                {
                    "helper_country_code": "UA",
                    "count": "9",
                    "items": [
                        {
                            "id": 42,
                            "title": "Ignored without string id",
                            "url": "/requests/ignored",
                        },
                        {
                            "id": "REQ-1",
                            "title": "Archive request",
                            "url": "/requests/1",
                            "edit_url": "/requests/1/edit",
                            "interaction_url": "/interactions/1",
                            "status": "open",
                            "is_test": True,
                            "created_at": "2026-05-25T10:00:00Z",
                        },
                    ],
                }
            ]
        }
    )

    assert len(groups) == 1
    assert groups[0].count == 9
    assert len(groups[0].items) == 1
    assert groups[0].items[0].url == f"{API_BASE_URL}/requests/1"
    assert groups[0].items[0].edit_url == f"{API_BASE_URL}/requests/1/edit"
    assert groups[0].items[0].is_test is True


def test_parse_genealogy_requests_normalizes_string_test_flags() -> None:
    """Verify parse genealogy requests normalizes string test flags."""
    groups = parse_genealogy_requests_response(
        {
            "data": [
                {
                    "helper_country_code": "UA",
                    "items": [
                        {
                            "id": "REQ-1",
                            "title": "Real request",
                            "url": "/requests/1",
                            "is_test": "0",
                        },
                        {
                            "id": "REQ-2",
                            "title": "Test request",
                            "url": "/requests/2",
                            "is_test": "true",
                        },
                    ],
                }
            ]
        }
    )

    assert [item.is_test for item in groups[0].items] == [False, True]


def test_request_list_badges_prefer_test_marker_over_status() -> None:
    """Verify request list badges prefer test marker over status."""
    label, markup = request_item_status_badge(
        GenealogyRequestItem(
            id="REQ-1",
            title="Test request",
            url="/requests/1",
            status="active",
            is_test=True,
        )
    )

    assert label == "Test"
    assert "#ede9fe" in markup
    assert status_badge("in_progress")[0] == "In progress"
    assert display_datetime("2026-05-25T10:15:30Z") == "2026-05-25 10:15"


def test_status_badge_escapes_markup_and_template_formatting_falls_back() -> None:
    """Verify status badges escape markup and title formatting tolerates missing keys."""
    label, markup = status_badge("<unknown>")

    assert label == "<unknown>"
    assert "&lt;unknown&gt;" in markup
    assert format_template("Find records for {name}", {"name": "Poltava"}) == (
        "Find records for Poltava"
    )
    assert format_template("Find records for {missing}", {}) == "Find records for {missing}"


def test_note_description_uses_note_text_directly() -> None:
    """Verify note description uses note text directly."""
    context = note_extractor.extract_note(None, FakeNote("  Research assumption  "), "note-1")

    assert context.nav_type == "Note"
    assert context.handle == "note-1"
    assert context.description == "Research assumption"


def test_media_description_includes_date_attributes_notes_and_file_path(
    monkeypatch,
    tmp_path,
) -> None:
    """Verify media description includes date attributes notes and file path."""
    media_path = tmp_path / "photo.jpg"
    media_path.write_bytes(b"JPEGDATA")
    monkeypatch.setattr(media_extractor, "media_path_full", lambda _db, path: path)
    monkeypatch.setattr(media_extractor, "get_gramps_date", lambda _media: "1897")
    db = FakeCitationDb({"media-note": FakeNote("Back side note")})
    media = FakeMedia(
        str(media_path),
        note_handles=["media-note"],
        attributes=[FakeAttribute("Archive", "State Archive")],
    )

    context = media_extractor.extract_media(db, media, "media-1")

    assert context.nav_type == "Media"
    assert context.file_path == str(media_path)
    assert not context.warnings
    assert context.description == expected_description(
        [
            "Date: 1897",
        ],
        [
            "Document attributes:",
            "- Archive: State Archive",
        ],
        [
            "Notes:",
            "- Back side note",
        ],
    )


def test_media_extractor_warns_when_file_is_missing(monkeypatch) -> None:
    """Verify media extractor warns when file is missing."""
    monkeypatch.setattr(media_extractor, "media_path_full", lambda _db, path: path)
    monkeypatch.setattr(media_extractor, "get_gramps_date", lambda _media: "")

    context = media_extractor.extract_media(
        FakeCitationDb({}),
        FakeMedia("/tmp/missing-genehelp-file.jpg"),
        "media-1",
    )

    assert context.file_path is None
    assert context.warnings == ["The active media file was not found on disk."]


def test_media_extractor_warns_for_unsupported_extension(monkeypatch, tmp_path) -> None:
    """Verify media extractor rejects unsupported file extensions."""
    media_path = tmp_path / "document.gif"
    media_path.write_bytes(b"GIF")
    monkeypatch.setattr(media_extractor, "media_path_full", lambda _db, path: path)
    monkeypatch.setattr(media_extractor, "get_gramps_date", lambda _media: "")

    context = media_extractor.extract_media(
        FakeCitationDb({}),
        FakeMedia(str(media_path)),
        "media-1",
    )

    assert context.file_path is None
    assert context.warnings == ["Only JPG, PNG, or WebP images are supported."]


def test_media_extractor_warns_for_too_large_file(monkeypatch, tmp_path) -> None:
    """Verify media extractor rejects files larger than the API limit."""
    media_path = tmp_path / "document.jpg"
    media_path.write_bytes(b"x" * (media_extractor.MAX_MEDIA_BYTES + 1))
    monkeypatch.setattr(media_extractor, "media_path_full", lambda _db, path: path)
    monkeypatch.setattr(media_extractor, "get_gramps_date", lambda _media: "")

    context = media_extractor.extract_media(
        FakeCitationDb({}),
        FakeMedia(str(media_path)),
        "media-1",
    )

    assert context.file_path is None
    assert context.warnings == ["The file cannot be larger than 3 MB."]


def test_repository_description_includes_type_urls_and_notes() -> None:
    """Verify repository description includes type urls and notes."""
    db = FakeCitationDb({"repo-note": FakeNote("Ask about digitization policy")})
    repository = FakeRepository(
        "Central Archive",
        repo_type="Archive",
        urls=[
            FakeRepositoryUrl(
                "Web Home",
                "Finding aids",
                "https://archive.example.test",
            )
        ],
        note_handles=["repo-note"],
    )

    context = repository_extractor.extract_repository(db, repository, "repo-1")

    assert context.nav_type == "Repository"
    assert context.title_values == {"name": "Central Archive"}
    assert context.description == expected_description(
        [
            "Name: Central Archive",
            "Type: Archive",
        ],
        [
            "Online records:",
            "- Web Home - Finding aids - https://archive.example.test",
        ],
        [
            "Notes:",
            "- Ask about digitization policy",
        ],
    )


def test_reference_handle_supports_ref_attribute_method_and_none() -> None:
    """Verify reference handle helper supports Gramps reference shapes."""

    class MethodRef:
        """Reference test double exposing only get_reference_handle."""

        @staticmethod
        def get_reference_handle() -> str:
            """Return reference handle."""
            return "x"

    assert reference_handle(FakeRef("event-1")) == "event-1"
    assert reference_handle(MethodRef()) == "x"
    assert reference_handle(None) == ""
    assert reference_handle(object()) == ""


def test_attribute_texts_supports_regular_and_source_attribute_types() -> None:
    """Verify attribute text labels support Gramps AttributeType and SrcAttributeType."""

    class RegularAttributeType:
        """AttributeType-like test double."""

        def type2base(self) -> str:
            """Return regular attribute base label."""
            return "Occupation"

    class SourceAttributeType:
        """SrcAttributeType-like test double."""

        string = "Archive"

    class AttributeOwner:
        """Attribute owner test double."""

        def get_attribute_list(self):
            """Return mixed attribute list."""
            return [
                FakeAttribute(RegularAttributeType(), "Blacksmith"),
                FakeAttribute(SourceAttributeType(), "State Archive"),
                FakeAttribute("Record ID", "42"),
            ]

    assert attribute_texts(AttributeOwner()) == [
        "Occupation: Blacksmith",
        "Archive: State Archive",
        "Record ID: 42",
    ]


def test_citation_description_includes_source_notes_and_attributes(monkeypatch) -> None:
    """Verify citation description includes source notes and attributes."""
    monkeypatch.setattr(citation_extractor, "get_gramps_date", lambda _citation: "1897")

    db = FakeCitationDb(
        {
            "citation-note": FakeNote("Citation note text"),
            "source-note": FakeNote("Source note text"),
        }
    )
    source = FakeSource(
        title="Civil register",
        author="Archive author",
        note_handles=["source-note"],
        attributes=[FakeAttribute("Archive", "State Archive")],
    )
    citation = FakeCitation(
        source_handle="source-1",
        page="vol. 2, p. 15",
        note_handles=["citation-note"],
        attributes=[FakeAttribute("Record ID", "42")],
    )
    db.sources["source-1"] = source

    context = citation_extractor.extract_citation(db, citation, "citation-1")

    assert context.nav_type == "Citation"
    assert context.description == expected_description(
        [
            "Source title: Civil register",
            "Source author: Archive author",
        ],
        [
            "Date: 1897",
            "Volume/Page: vol. 2, p. 15",
        ],
        [
            "Citation notes:",
            "- Citation note text",
        ],
        [
            "Source notes:",
            "- Source note text",
        ],
        [
            "Citation attributes:",
            "- Record ID: 42",
        ],
        [
            "Source attributes:",
            "- Archive: State Archive",
        ],
    )


def test_source_description_includes_repositories_notes_and_attributes() -> None:
    """Verify source description includes repositories notes and attributes."""
    db = FakeCitationDb({"source-note": FakeNote("Source note text")})
    db.repositories["repo-1"] = FakeRepository("Central Archive")
    db.repositories["repo-2"] = FakeRepository("Old Cemetery")
    source = FakeSource(
        title="Civil register",
        author="Archive author",
        publication_info="Kyiv, 1897",
        abbreviation="CR",
        note_handles=["source-note"],
        attributes=[FakeAttribute("Fond", "123")],
        repo_refs=[FakeRepoRef("repo-1"), FakeRepoRef("repo-2")],
    )

    context = source_extractor.extract_source(db, source, "source-1")

    assert context.nav_type == "Source"
    assert context.description == expected_description(
        [
            "Title: Civil register",
            "Author: Archive author",
            "Publication info: Kyiv, 1897",
            "Abbreviation: CR",
        ],
        [
            "Source attributes:",
            "- Fond: 123",
        ],
        [
            "Repositories:",
            "- Central Archive",
            "- Old Cemetery",
        ],
        [
            "Notes:",
            "- Source note text",
        ],
    )


def test_place_description_includes_full_name_coordinates_alternatives_and_notes(
    monkeypatch,
) -> None:
    """Verify place description includes full name coordinates alternatives and notes."""
    monkeypatch.setattr(
        place_extractor.place_displayer,
        "display",
        lambda _db, _place: "Poltava, Poltava Raion, Poltava Oblast, Ukraine",
    )
    db = FakeCitationDb({"place-note": FakeNote("Place note text")})
    place = FakePlace(
        primary_name="Poltava",
        alternative_names=["Ltava", "Pultawa"],
        latitude="49.5883",
        longitude="34.5514",
        note_handles=["place-note"],
    )

    context = place_extractor.extract_place(db, place, "place-1")

    assert context.nav_type == "Place"
    assert context.title_values == {"name": "Poltava"}
    assert context.description == expected_description(
        [
            "Full place name: Poltava, Poltava Raion, Poltava Oblast, Ukraine",
            "Coordinates: 49.58830000, 34.55140000",
            "Google Maps: https://www.google.com/maps/place/?q=49.58830000,34.55140000",
        ],
        [
            "Alternative names:",
            "- Ltava",
            "- Pultawa",
        ],
        [
            "Notes:",
            "- Place note text",
        ],
    )


def test_place_description_omits_map_when_coordinates_are_missing(monkeypatch) -> None:
    """Verify place description omits Google Maps link without full coordinates."""
    monkeypatch.setattr(
        place_extractor.place_displayer,
        "display",
        lambda _db, _place: "Unknown village, Ukraine",
    )
    place = FakePlace(
        primary_name="",
        alternative_names=["Alias", ""],
        latitude="",
        longitude="34.5514",
        note_handles=[],
    )

    context = place_extractor.extract_place(FakeCitationDb({}), place, "place-1")

    assert context.title_values == {"name": "Unknown village, Ukraine"}
    assert "Google Maps:" not in context.description
    assert context.description == expected_description(
        [
            "Full place name: Unknown village, Ukraine",
        ],
        [
            "Alternative names:",
            "- Alias",
        ],
    )


def test_event_description_includes_type_date_place_notes_attributes_and_people(
    monkeypatch,
) -> None:
    """Verify event description includes type date place notes attributes and people."""
    monkeypatch.setattr(
        gramps_event_helpers,
        "get_gramps_date",
        lambda _event: "12 May 1897",
    )
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

    db = FakeCitationDb({"event-note": FakeNote("Event note text")})
    db.places["place-1"] = FakeRepository("Poltava")
    db.people["person-1"] = FakePerson("Ivan Petrenko")
    db.people["person-2"] = FakePerson("Maria Petrenko")
    db.families["family-1"] = FakeFamily("person-1", "person-2")
    db.backlinks["event-1"] = [("Family", "family-1")]
    event = FakeEvent(
        handle="event-1",
        event_type="Marriage",
        date="",
        description="Church wedding",
        place_handle="place-1",
        note_handles=["event-note"],
        attributes=[FakeAttribute("Witness", "Petro Ivanenko")],
    )

    context = event_extractor.extract_event(db, event, "event-1")

    assert context.nav_type == "Event"
    assert context.title_values == {
        "event_type": "Marriage",
        "people": "Ivan Petrenko, Maria Petrenko",
    }
    assert context.description == "\n".join(
        [
            "Event type: Marriage",
            "Date: 12 May 1897",
            "Description: Church wedding",
            "Place: Poltava, Poltava Oblast, Ukraine",
            "Notes:",
            "- Event note text",
            "Event attributes:",
            "- Witness: Petro Ivanenko",
        ]
    )


def test_event_people_text_combines_direct_person_and_family_backlinks(monkeypatch) -> None:
    """Verify event people text supports person and family backlinks without duplicates."""
    monkeypatch.setattr(
        gramps_people_helpers.name_displayer,
        "display",
        lambda person: person.name,
    )
    db = FakeCitationDb({})
    db.people["person-1"] = FakePerson("Ivan Petrenko")
    db.people["person-2"] = FakePerson("Maria Petrenko")
    db.families["family-1"] = FakeFamily("person-1", "person-2")
    db.backlinks["event-1"] = [
        ("Person", "person-1"),
        ("Family", "family-1"),
        ("Citation", "ignored"),
    ]
    event = FakeEvent("event-1", "Birth", "", "", "", [], [])

    assert event_extractor.event_people_text(db, event) == "Ivan Petrenko, Maria Petrenko"


def test_event_title_values_fallback_for_missing_people_and_type(monkeypatch) -> None:
    """Verify event title values use readable fallbacks for sparse events."""
    monkeypatch.setattr(gramps_event_helpers, "get_gramps_date", lambda _event: "")
    event = FakeEvent("event-1", "", "", "", "", [], [])

    context = event_extractor.extract_event(FakeCitationDb({}), event, "event-1")

    assert context.title_values == {
        "event_type": "event",
        "people": "selected people",
    }
