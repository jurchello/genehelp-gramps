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

"""Place extraction for GeneHelp request drafts."""

from typing import Any

from gramps.gen.display.place import displayer as place_displayer
from gramps.gen.utils.place import conv_lat_lon

from genehelp.config import DATA_SOURCE_PLACE
from genehelp.extractors.common import bullet_texts, compact_description, note_texts, titled_block
from genehelp.l10n import _
from genehelp.models import ImportedContext


def extract_place(db: Any, place: Any, handle: str) -> ImportedContext:
    """Extract place."""
    short_name = place_short_name(db, place)
    return ImportedContext(
        nav_type=DATA_SOURCE_PLACE,
        handle=handle,
        description=build_place_text(db, place),
        title_values={"name": short_name},
    )


def build_place_text(db: Any, place: Any) -> str:
    """Build place text."""
    metadata = []

    full_name = place_full_name(db, place)
    if full_name:
        metadata.append(_("Full place name: %s") % full_name)

    coordinates = place_coordinates(place)
    if coordinates is not None:
        latitude, longitude = coordinates
        metadata.append(_("Coordinates: %s, %s") % (latitude, longitude))
        metadata.append(_("Google Maps: %s") % google_maps_url(latitude, longitude))

    alternative_names = place_alternative_names(place)
    notes = note_texts(db, place.get_note_list())

    return compact_description(
        [
            metadata,
            titled_block(_("Alternative names:"), bullet_texts(alternative_names)),
            titled_block(_("Notes:"), bullet_texts(notes)),
        ]
    )


def place_short_name(db: Any, place: Any) -> str:
    """Place short name."""
    primary_name = place.get_name()
    if primary_name is not None:
        value = (primary_name.get_value() or "").strip()
        if value:
            return value
    return place_full_name(db, place) or _("locality")


def place_full_name(db: Any, place: Any) -> str:
    """Place full name."""
    return (place_displayer.display(db, place) or "").strip()


def place_alternative_names(place: Any) -> list[str]:
    """Place alternative names."""
    names = []
    for place_name in place.get_alternative_names():
        value = (place_name.get_value() or "").strip()
        if value:
            names.append(value)
    return names


def place_coordinates(place: Any) -> tuple[str, str] | None:
    """Place coordinates."""
    latitude = (place.get_latitude() or "").strip()
    longitude = (place.get_longitude() or "").strip()
    if not latitude or not longitude:
        return None

    converted_latitude, converted_longitude = conv_lat_lon(latitude, longitude, "D.D8")
    if not converted_latitude or not converted_longitude:
        return None
    return converted_latitude, converted_longitude


def google_maps_url(latitude: str, longitude: str) -> str:
    """Google maps url."""
    return f"https://www.google.com/maps/place/?q={latitude},{longitude}"
