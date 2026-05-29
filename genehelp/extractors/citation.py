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

"""Citation extraction for GeneHelp request drafts."""

from typing import Any

from gramps.gen.datehandler import get_date as get_gramps_date

from genehelp.config import DATA_SOURCE_CITATION
from genehelp.extractors.common import (
    attribute_texts,
    bullet_texts,
    compact_description,
    note_texts,
    titled_block,
)
from genehelp.l10n import _
from genehelp.models import ImportedContext


def extract_citation(db: Any, citation: Any, handle: str) -> ImportedContext:
    """Extract citation."""
    source = source_for_citation(db, citation)
    return ImportedContext(
        nav_type=DATA_SOURCE_CITATION,
        handle=handle,
        description=build_citation_text(db, citation, source),
    )


def source_for_citation(db: Any, citation: Any) -> Any:
    """Source for citation."""
    source_handle = citation.get_reference_handle()
    if not source_handle:
        return None
    return db.get_source_from_handle(source_handle)


def build_citation_text(db: Any, citation: Any, source: Any) -> str:
    """Build citation text."""
    blocks = []
    source_lines = []

    if source is not None:
        source_title = (source.get_title() or "").strip()
        source_author = (source.get_author() or "").strip()
        if source_title:
            source_lines.append(_("Source title: %s") % source_title)
        if source_author:
            source_lines.append(_("Source author: %s") % source_author)
    blocks.append(source_lines)

    citation_lines = []
    citation_date = get_gramps_date(citation).strip()
    citation_page = (citation.get_page() or "").strip()
    if citation_date:
        citation_lines.append(_("Date: %s") % citation_date)
    if citation_page:
        citation_lines.append(_("Volume/Page: %s") % citation_page)
    blocks.append(citation_lines)

    citation_notes = note_texts(db, citation.get_note_list())
    blocks.append(titled_block(_("Citation notes:"), bullet_texts(citation_notes)))

    if source is not None:
        source_notes = note_texts(db, source.get_note_list())
        blocks.append(titled_block(_("Source notes:"), bullet_texts(source_notes)))

    citation_attributes = attribute_texts(citation)
    blocks.append(titled_block(_("Citation attributes:"), bullet_texts(citation_attributes)))

    if source is not None:
        source_attributes = attribute_texts(source)
        blocks.append(titled_block(_("Source attributes:"), bullet_texts(source_attributes)))

    return compact_description(blocks)
