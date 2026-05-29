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

"""Extractor registry for supported Gramps object types."""

from genehelp.extractors.citation import extract_citation
from genehelp.extractors.event import extract_event
from genehelp.extractors.family import extract_family
from genehelp.extractors.media import extract_media
from genehelp.extractors.note import extract_note
from genehelp.extractors.person import extract_person
from genehelp.extractors.place import extract_place
from genehelp.extractors.repository import extract_repository
from genehelp.extractors.source import extract_source

__all__ = [
    "extract_citation",
    "extract_event",
    "extract_family",
    "extract_media",
    "extract_note",
    "extract_person",
    "extract_place",
    "extract_repository",
    "extract_source",
]
