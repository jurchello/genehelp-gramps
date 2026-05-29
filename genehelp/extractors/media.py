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

"""Media extraction for GeneHelp request drafts."""

import os
from typing import Any

from gramps.gen.datehandler import get_date as get_gramps_date
from gramps.gen.utils.file import media_path_full

from genehelp.config import DATA_SOURCE_MEDIA, MAX_MEDIA_BYTES, SUPPORTED_EXTENSIONS
from genehelp.extractors.common import (
    attribute_texts,
    bullet_texts,
    compact_description,
    note_texts,
    titled_block,
)
from genehelp.l10n import _
from genehelp.models import ImportedContext


def extract_media(db: Any, media: Any, handle: str) -> ImportedContext:
    """Extract media."""
    warnings = []
    path = media_path_full(db, media.get_path())
    if not path or not os.path.isfile(path):
        warnings.append(_("The active media file was not found on disk."))
        path = None
    elif os.path.splitext(path)[1].lower() not in SUPPORTED_EXTENSIONS:
        warnings.append(_("Only JPG, PNG, or WebP images are supported."))
        path = None
    elif os.path.getsize(path) > MAX_MEDIA_BYTES:
        warnings.append(_("The file cannot be larger than 3 MB."))
        path = None

    return ImportedContext(
        nav_type=DATA_SOURCE_MEDIA,
        handle=handle,
        description=build_media_text(db, media),
        file_path=path,
        warnings=warnings,
    )


def build_media_text(db: Any, media: Any) -> str:
    """Build media text."""
    metadata = []
    date_text = get_gramps_date(media).strip()
    if date_text:
        metadata.append(_("Date: %s") % date_text)

    attributes = attribute_texts(media)
    notes = note_texts(db, media.get_note_list())

    return compact_description(
        [
            metadata,
            titled_block(_("Document attributes:"), bullet_texts(attributes)),
            titled_block(_("Notes:"), bullet_texts(notes)),
        ]
    )
