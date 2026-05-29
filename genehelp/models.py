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

"""Data objects shared across the GeneHelp gramplet."""

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class ThemeOption:
    """Request topic template available for one Gramps page type.
    It links a UI radio button, API theme value, and default title template.
    """

    key: str
    api_theme: str
    label: str
    default_title: str
    button_id: str


@dataclass
class ImportedContext:
    """Extracted Gramps object data prepared for request creation.
    It contains the source page type, editable description, title values, and media path.
    """

    nav_type: str
    handle: str
    description: str
    file_path: Optional[str] = None
    title_values: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SubmitPayload:
    """Multipart request payload sent to the GeneHelp integration API.
    It keeps text fields separate from the optional media file path.
    """

    fields: dict[str, str]
    file_field: str
    file_path: Optional[str] = None


@dataclass(frozen=True)
class CountryOption:
    """Localized country option returned by the country API."""

    code: str
    name: str


@dataclass(frozen=True)
class GenealogyRequestItem:
    """Single genealogy request row returned for the owner request list."""

    id: str
    title: str
    url: str
    edit_url: str = ""
    status: str = ""
    is_test: bool = False
    created_at: str = ""
    interaction_url: str = ""


@dataclass(frozen=True)
class GenealogyRequestGroup:
    """Group of genealogy requests sharing the same helper country."""

    helper_country_code: str
    count: int
    items: tuple[GenealogyRequestItem, ...]


@dataclass(frozen=True)
class HelpOfferEnabledValue:
    """Enabled or disabled labeled value inside a help profile section."""

    key: str
    label: str
    description: str = ""
    enabled: bool = False


@dataclass(frozen=True)
class HelpOfferHistoricalPeriod:
    """Historical period item from a localized help profile section."""

    key: str
    selection_type: str
    selection_type_label: str = ""
    label: str = ""
    enabled: bool = True
    range_key: str = ""
    context_key: str = ""
    from_year: Optional[int] = None
    to_year: Optional[int] = None


@dataclass(frozen=True)
class HelpOfferDocumentType:
    """Document type item from a localized help profile section."""

    key: str
    label: str = ""
    enabled: bool = True


@dataclass(frozen=True)
class HelpOfferAccessPoint:
    """Place or institution where the helper can provide online or physical support."""

    location_type: str
    country_code: str
    location_type_label: str = ""
    place_name: str = ""
    region: str = ""
    district: str = ""
    region_wide: bool = False
    administrative_area_name: str = ""
    object_type_label: str = ""
    object_name: str = ""
    radius_km: Optional[int] = None
    purpose: str = ""


@dataclass(frozen=True)
class HelpOfferSection:
    """Localized help profile section with typed renderer metadata."""

    key: str
    label: str
    type: str
    items: tuple[Any, ...]


@dataclass(frozen=True)
class HelpOffer:
    """Complete help profile payload rendered in the gramplet."""

    user_id: str
    profile_url: str
    can_online: bool
    can_offline: bool
    helper_country_code: str
    helper_country_source: str
    channels: tuple[HelpOfferEnabledValue, ...]
    conditions: tuple[HelpOfferEnabledValue, ...]
    capabilities: tuple[HelpOfferEnabledValue, ...]
    historical_periods: tuple[HelpOfferHistoricalPeriod, ...]
    document_types: tuple[HelpOfferDocumentType, ...]
    access_points: tuple[HelpOfferAccessPoint, ...]
    sections: tuple[HelpOfferSection, ...] = ()


Extractor = Callable[[Any, Any, str], ImportedContext]


@dataclass(frozen=True)
class PageHandler:
    """Declarative binding between a Gramps page type, extractor, and request templates."""

    nav_type: str
    object_getter_name: str
    theme_box_id: str
    theme_section_label_id: str
    themes: tuple[ThemeOption, ...]
    extractor: Extractor
