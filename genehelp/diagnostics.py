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

"""Console diagnostics for unexpected GeneHelp gramplet errors."""

import sys
import traceback


def print_error_diagnostic(message: str) -> None:
    """Print error diagnostic."""
    print(message, file=sys.stderr)


def print_exception_diagnostic(message: str) -> None:
    """Print exception diagnostic."""
    print_error_diagnostic(message)
    print(traceback.format_exc(), file=sys.stderr)
