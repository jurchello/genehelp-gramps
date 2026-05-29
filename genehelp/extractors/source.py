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

"""Source extraction for GeneHelp request drafts."""

from typing import Any

from genehelp.config import DATA_SOURCE_SOURCE
from genehelp.extractors.common import (
    attribute_texts,
    bullet_texts,
    compact_description,
    note_texts,
    titled_block,
)
from genehelp.l10n import _
from genehelp.models import ImportedContext


def extract_source(db: Any, source: Any, handle: str) -> ImportedContext:
    """Extract source."""
    return ImportedContext(
        nav_type=DATA_SOURCE_SOURCE,
        handle=handle,
        description=build_source_text(db, source),
    )


def build_source_text(db: Any, source: Any) -> str:
    """Build source text."""
    metadata = []

    source_title = (source.get_title() or "").strip()
    source_author = (source.get_author() or "").strip()
    publication_info = (source.get_publication_info() or "").strip()
    abbreviation = (source.get_abbreviation() or "").strip()
    if source_title:
        metadata.append(_("Title: %s") % source_title)
    if source_author:
        metadata.append(_("Author: %s") % source_author)
    if publication_info:
        metadata.append(_("Publication info: %s") % publication_info)
    if abbreviation:
        metadata.append(_("Abbreviation: %s") % abbreviation)

    attributes = attribute_texts(source)
    repository_names = source_repository_names(db, source)
    notes = note_texts(db, source.get_note_list())

    return compact_description(
        [
            metadata,
            titled_block(_("Source attributes:"), bullet_texts(attributes)),
            titled_block(_("Repositories:"), bullet_texts(repository_names)),
            titled_block(_("Notes:"), bullet_texts(notes)),
        ]
    )


def source_repository_names(db: Any, source: Any) -> list[str]:
    """Source repository names."""
    names = []
    for repo_ref in source.get_reporef_list():
        repo_handle = repo_ref.get_reference_handle()
        if not repo_handle:
            continue
        repository = db.get_repository_from_handle(repo_handle)
        if repository is None:
            continue
        name = (repository.get_name() or "").strip()
        if name:
            names.append(name)
    return names
