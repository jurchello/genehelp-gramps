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

"""Note extraction for GeneHelp request drafts."""

from typing import Any

from genehelp.config import DATA_SOURCE_NOTE
from genehelp.models import ImportedContext


def extract_note(_db: Any, note: Any, handle: str) -> ImportedContext:
    """Extract note."""
    note_text = note.get().strip()
    return ImportedContext(
        nav_type=DATA_SOURCE_NOTE,
        handle=handle,
        description=note_text,
    )
