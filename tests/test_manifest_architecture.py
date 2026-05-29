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

"""Architecture checks for the Gramps addon manifest."""

from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[1]
ADDON_NAME = ROOT.name
MANIFEST_PATH = ROOT / "MANIFEST"

GRAMPS_AUTO_INCLUDED_SUFFIXES = {".glade", ".py", ".txt", ".xml"}
GRAMPS_AUTO_INCLUDED_LOCALE_RE = re.compile(r"^locale/[^/]+/LC_MESSAGES/[^/]+\.mo$")

RUNTIME_RESOURCES = {
    ROOT / "Genehelp.css",
}
RUNTIME_RESOURCE_PATTERNS = {
    f"{ADDON_NAME}/genehelp/*.py",
    f"{ADDON_NAME}/genehelp/extractors/*.py",
}


def test_manifest_matches_required_runtime_resources() -> None:
    """Verify manifest matches required runtime resources."""
    entries = manifest_entries()
    required_entries = {
        manifest_entry(path)
        for path in RUNTIME_RESOURCES
        if not gramps_auto_includes(path.relative_to(ROOT))
    } | RUNTIME_RESOURCE_PATTERNS

    assert entries == required_entries


def test_manifest_entries_are_concrete_existing_addon_files() -> None:
    """Verify manifest entries are concrete existing addon files."""
    entries = manifest_entries()
    violations = []

    for entry in sorted(entries):
        if entry.startswith("/") or ".." in Path(entry).parts:
            violations.append(f"{entry}: entry must be a relative addon path")
            continue
        if not entry.startswith(f"{ADDON_NAME}/"):
            violations.append(f"{entry}: entry must be prefixed with {ADDON_NAME}/")
            continue

        if "*" in entry:
            if not sorted(ROOT.parent.glob(entry)):
                violations.append(f"{entry}: wildcard pattern does not match files")
            continue

        local_path = ROOT / Path(entry).relative_to(ADDON_NAME)
        if not local_path.is_file():
            violations.append(f"{entry}: target file does not exist")
            continue
        if gramps_auto_includes(local_path.relative_to(ROOT)):
            violations.append(f"{entry}: Gramps already includes this file type")

    if violations:
        pytest.fail("MANIFEST contains invalid entries:\n" + "\n".join(violations))


def test_manifest_packaging_smoke_includes_runtime_and_excludes_development_files() -> None:
    """Verify Gramps packaging patterns include runtime files and exclude dev files."""
    packaged_files = simulated_packaged_files()

    assert f"{ADDON_NAME}/Genehelp.py" in packaged_files
    assert f"{ADDON_NAME}/Genehelp.gpr.py" in packaged_files
    assert f"{ADDON_NAME}/Genehelp.xml" in packaged_files
    assert f"{ADDON_NAME}/Genehelp.css" in packaged_files
    assert f"{ADDON_NAME}/genehelp/ui.py" in packaged_files
    assert f"{ADDON_NAME}/genehelp/extractors/person.py" in packaged_files
    assert f"{ADDON_NAME}/tests/test_api_logic.py" not in packaged_files
    assert f"{ADDON_NAME}/docs/architecture.md" not in packaged_files
    assert f"{ADDON_NAME}/po/template.pot" not in packaged_files


def manifest_entries() -> set[str]:
    """Manifest entries."""
    assert MANIFEST_PATH.is_file(), "MANIFEST is required for non-Python runtime resources."
    raw_entries = MANIFEST_PATH.read_text(encoding="utf-8").split()
    duplicates = sorted({entry for entry in raw_entries if raw_entries.count(entry) > 1})
    assert not duplicates, "MANIFEST contains duplicate entries: " + ", ".join(duplicates)
    return set(raw_entries)


def manifest_entry(path: Path) -> str:
    """Manifest entry."""
    return f"{ADDON_NAME}/{path.relative_to(ROOT).as_posix()}"


def gramps_auto_includes(relative_path: Path) -> bool:
    """Gramps auto includes."""
    path_text = relative_path.as_posix()
    if len(relative_path.parts) != 1:
        return GRAMPS_AUTO_INCLUDED_LOCALE_RE.match(path_text) is not None
    return (
        relative_path.suffix in GRAMPS_AUTO_INCLUDED_SUFFIXES
        or GRAMPS_AUTO_INCLUDED_LOCALE_RE.match(path_text) is not None
    )


def simulated_packaged_files() -> set[str]:
    """Simulated packaged files using Gramps make.py glob rules."""
    patterns = [
        f"{ADDON_NAME}/*.py",
        f"{ADDON_NAME}/*.glade",
        f"{ADDON_NAME}/*.xml",
        f"{ADDON_NAME}/*.txt",
        f"{ADDON_NAME}/locale/*/LC_MESSAGES/*.mo",
        *manifest_entries(),
    ]
    packaged = set()
    for pattern in patterns:
        for path in ROOT.parent.glob(pattern):
            if path.is_file():
                packaged.add(path.relative_to(ROOT.parent).as_posix())
    return packaged
