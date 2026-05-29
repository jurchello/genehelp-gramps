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

"""Repository extraction for GeneHelp request drafts."""

from typing import Any

from genehelp.config import DATA_SOURCE_REPOSITORY
from genehelp.extractors.common import bullet_texts, compact_description, note_texts, titled_block
from genehelp.l10n import _
from genehelp.models import ImportedContext


def extract_repository(db: Any, repository: Any, handle: str) -> ImportedContext:
    """Extract repository."""
    name = repository_name(repository)
    return ImportedContext(
        nav_type=DATA_SOURCE_REPOSITORY,
        handle=handle,
        description=build_repository_text(db, repository),
        title_values={"name": name},
    )


def repository_name(repository: Any) -> str:
    """Repository name."""
    return (repository.get_name() or "").strip() or _("archive")


def build_repository_text(db: Any, repository: Any) -> str:
    """Build repository text."""
    metadata = []
    name = (repository.get_name() or "").strip()
    repo_type = str(repository.get_type()).strip()

    if name:
        metadata.append(_("Name: %s") % name)
    if repo_type:
        metadata.append(_("Type: %s") % repo_type)

    urls = []
    for url in repository.get_url_list():
        url_path = (url.get_full_path() or "").strip()
        url_type = str(url.get_type()).strip()
        url_description = (url.get_description() or "").strip()
        parts = [part for part in [url_type, url_description, url_path] if part]
        if parts:
            urls.append(" - ".join(parts))
    notes = note_texts(db, repository.get_note_list())

    return compact_description(
        [
            metadata,
            titled_block(_("Online records:"), bullet_texts(urls)),
            titled_block(_("Notes:"), bullet_texts(notes)),
        ]
    )
