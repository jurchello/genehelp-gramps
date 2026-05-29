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

"""Architecture checks for repository text files."""

import ast
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import pytest

from genehelp.themes import PAGE_HANDLERS


ROOT = Path(__file__).resolve().parents[1]
CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")
TEXT_SUFFIXES = {
    ".css",
    ".md",
    ".pot",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
TEXT_FILENAMES = {
    ".gitignore",
    "MANIFEST",
    "pylintrc",
}
EXCLUDED_DIRS = {
    ".agents",
    ".codex",
    ".git",
    ".idea",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
}
RUNTIME_PYTHON_FILES = [
    ROOT / "Genehelp.py",
    ROOT / "Genehelp.gpr.py",
    *ROOT.glob("genehelp/*.py"),
    *ROOT.glob("genehelp/extractors/*.py"),
]


def repository_text_files() -> list[Path]:
    """Repository text files."""
    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if EXCLUDED_DIRS.intersection(path.relative_to(ROOT).parts):
            continue
        if path.suffix in TEXT_SUFFIXES or path.name in TEXT_FILENAMES:
            files.append(path)
    return sorted(files)


def test_repository_text_files_do_not_contain_cyrillic() -> None:
    """Verify repository text files do not contain cyrillic."""
    matches = []
    for path in repository_text_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if CYRILLIC_RE.search(line):
                relative_path = path.relative_to(ROOT)
                matches.append(f"{relative_path}:{line_number}: {line}")

    if matches:
        pytest.fail(
            "Repository text files should not contain Cyrillic characters:\n" + "\n".join(matches)
        )


def test_gtk_builder_does_not_own_translatable_strings() -> None:
    """Verify gtk builder does not own translatable strings."""
    translatable_properties = [
        property_node.text or ""
        for property_node in ET.parse(ROOT / "Genehelp.xml").iter("property")
        if property_node.attrib.get("translatable") == "yes"
    ]

    assert translatable_properties == []


def test_gtk_builder_contains_all_theme_handler_widgets() -> None:
    """Verify gtk builder contains all theme handler widgets."""
    object_ids = {
        object_node.attrib["id"]
        for object_node in ET.parse(ROOT / "Genehelp.xml").iter("object")
        if "id" in object_node.attrib
    }
    expected_ids = set()
    for handler in PAGE_HANDLERS.values():
        expected_ids.add(handler.theme_box_id)
        expected_ids.add(handler.theme_section_label_id)
        expected_ids.update(theme.button_id for theme in handler.themes)

    assert sorted(expected_ids - object_ids) == []


def test_gtk_builder_theme_radio_buttons_match_registered_themes() -> None:
    """Verify gtk builder theme radio buttons match registered themes."""
    object_ids = {
        object_node.attrib["id"]
        for object_node in ET.parse(ROOT / "Genehelp.xml").iter("object")
        if "id" in object_node.attrib
    }
    registered_button_ids = {
        theme.button_id for handler in PAGE_HANDLERS.values() for theme in handler.themes
    }
    xml_theme_button_ids = {
        object_id
        for object_id in object_ids
        if "_theme_" in object_id and object_id.endswith("_radio")
    }

    assert sorted(xml_theme_button_ids - registered_button_ids) == []
    assert sorted(registered_button_ids - xml_theme_button_ids) == []


def test_gtk_builder_contains_required_form_and_tab_widgets() -> None:
    """Verify GTK builder owns all core workflow widgets expected by the UI binder."""
    object_ids = {
        object_node.attrib["id"]
        for object_node in ET.parse(ROOT / "Genehelp.xml").iter("object")
        if "id" in object_node.attrib
    }
    required_ids = {
        "test_request_checkbox",
        "request_country_combo",
        "helper_country_combo",
        "title_text_buffer",
        "request_text_buffer",
        "submit_button",
        "status_label",
        "requests_tree_view",
        "requests_refresh_button",
        "help_offer_profile_button",
        "help_offer_refresh_button",
        "info_text_view",
    }

    assert sorted(required_ids - object_ids) == []


def test_gtk_builder_user_visible_strings_are_empty_until_code_localizes_them() -> None:
    """Verify user-visible GTK labels are not hardcoded in XML."""
    allowed_nonempty_properties = {"orientation", "halign", "valign", "shadow-type"}
    allowed_literal_labels = {"GENEHELP"}
    violations = []
    for property_node in ET.parse(ROOT / "Genehelp.xml").iter("property"):
        name = property_node.attrib.get("name", "")
        text = (property_node.text or "").strip()
        if name in allowed_nonempty_properties or name not in {"label", "tooltip-text"}:
            continue
        if text in allowed_literal_labels:
            continue
        if text:
            violations.append(text)

    assert not violations


def test_runtime_code_does_not_use_python_logging() -> None:
    """Verify runtime code does not use python logging."""
    violations = []
    for path in sorted(RUNTIME_PYTHON_FILES):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if imports_logging(node):
                violations.append(f"{node_location(path, node)}: imports logging")
            if uses_logging_module(node):
                violations.append(f"{node_location(path, node)}: uses logging module")
            if defines_module_logger(tree, node):
                violations.append(f"{node_location(path, node)}: defines module logger")
            if calls_logger_method(node):
                violations.append(f"{node_location(path, node)}: calls logger method")

    if violations:
        pytest.fail(
            "Runtime code should not use Python logging or module-level loggers:\n"
            + "\n".join(violations)
        )


def test_print_is_limited_to_diagnostic_helpers() -> None:
    """Verify print is limited to diagnostic helpers."""
    allowed_prints = {
        ("genehelp/diagnostics.py", "print_error_diagnostic"),
        ("genehelp/diagnostics.py", "print_exception_diagnostic"),
    }
    violations = []

    for path in sorted(RUNTIME_PYTHON_FILES):
        relative_path = path.relative_to(ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parents = parent_by_child(tree)
        for node in ast.walk(tree):
            if not is_print_call(node):
                continue
            function_name = containing_function_name(node, parents)
            if (relative_path, function_name) not in allowed_prints:
                violations.append(
                    f"{node_location(path, node)}: print in {function_name or '<module>'}"
                )

    if violations:
        pytest.fail(
            "print() is only allowed in diagnostics diagnostic helpers:\n" + "\n".join(violations)
        )


def test_runtime_code_does_not_import_or_start_gramps_db_transactions() -> None:
    """Verify runtime code cannot open write transactions against the Gramps database."""
    violations = []
    for path in sorted(RUNTIME_PYTHON_FILES):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if imports_gramps_db_transaction(node):
                violations.append(f"{node_location(path, node)}: imports Gramps DbTxn")
            if calls_name(node, "DbTxn"):
                violations.append(f"{node_location(path, node)}: starts Gramps DbTxn")

    if violations:
        pytest.fail(
            "GeneHelp must not open Gramps database write transactions:\n" + "\n".join(violations)
        )


def test_runtime_code_does_not_call_gramps_db_write_methods() -> None:
    """Verify runtime code does not add, commit, remove, or delete Gramps DB records."""
    violations: list[str] = []
    for path in sorted(RUNTIME_PYTHON_FILES):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        violations.extend(
            db_write_violation(path, node)
            for node in ast.walk(tree)
            if db_write_violation(path, node)
        )

    if violations:
        pytest.fail("GeneHelp must not write to the Gramps database:\n" + "\n".join(violations))


def test_extractors_do_not_call_gramps_object_mutation_methods() -> None:
    """Verify extractors only read Gramps objects and never mutate them."""
    extractor_files = sorted((ROOT / "genehelp" / "extractors").glob("*.py"))
    violations: list[str] = []
    for path in extractor_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        violations.extend(
            object_mutator_violation(path, node)
            for node in ast.walk(tree)
            if object_mutator_violation(path, node)
        )

    if violations:
        pytest.fail("GeneHelp extractors must not mutate Gramps objects:\n" + "\n".join(violations))


def imports_logging(node: ast.AST) -> bool:
    """Imports logging."""
    if isinstance(node, ast.Import):
        return any(alias.name == "logging" for alias in node.names)
    if isinstance(node, ast.ImportFrom):
        return node.module == "logging"
    return False


def imports_gramps_db_transaction(node: ast.AST) -> bool:
    """Imports Gramps DB transaction."""
    if not isinstance(node, ast.ImportFrom) or node.module != "gramps.gen.db":
        return False
    return any(alias.name == "DbTxn" for alias in node.names)


def calls_name(node: ast.AST, name: str) -> bool:
    """Return whether node calls a bare name."""
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == name


def calls_db_write_method(node: ast.AST) -> bool:
    """Return whether node calls a mutating Gramps database method."""
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return False
    method_name = node.func.attr
    if not method_name.startswith(("add_", "commit_", "remove_", "delete_")):
        return False
    return expression_targets_gramps_db(node.func.value)


def db_write_violation(path: Path, node: ast.AST) -> str:
    """Return DB write violation text for a node."""
    if not calls_db_write_method(node):
        return ""
    assert isinstance(node, ast.Call)
    assert isinstance(node.func, ast.Attribute)
    return f"{node_location(path, node)}: calls {node.func.attr} on DB"


def expression_targets_gramps_db(node: ast.AST) -> bool:
    """Return whether expression appears to be the Gramps database object."""
    if isinstance(node, ast.Name):
        return node.id == "db"
    if isinstance(node, ast.Attribute):
        if node.attr == "db":
            return True
        return expression_targets_gramps_db(node.value)
    return False


def calls_gramps_object_mutator(node: ast.AST) -> bool:
    """Return whether node calls a Gramps object mutation method."""
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return False
    method_name = node.func.attr
    if method_name.startswith(("add_", "remove_", "delete_")):
        return True
    return method_name in GRAMPS_OBJECT_MUTATOR_METHODS


def object_mutator_violation(path: Path, node: ast.AST) -> str:
    """Return object mutation violation text for a node."""
    if not calls_gramps_object_mutator(node):
        return ""
    assert isinstance(node, ast.Call)
    assert isinstance(node.func, ast.Attribute)
    return f"{node_location(path, node)}: calls {node.func.attr}"


GRAMPS_OBJECT_MUTATOR_METHODS = {
    "set_attribute_list",
    "set_birth_ref",
    "set_child_ref_list",
    "set_citation_list",
    "set_death_ref",
    "set_event_ref_list",
    "set_family_handle_list",
    "set_father_handle",
    "set_gender",
    "set_gramps_id",
    "set_media_list",
    "set_mother_handle",
    "set_note_list",
    "set_parent_family_handle_list",
    "set_person_ref_list",
    "set_place_handle",
    "set_primary_name",
    "set_reference_handle",
    "set_relationship",
    "set_tag_list",
    "set_value",
}


def uses_logging_module(node: ast.AST) -> bool:
    """Uses logging module."""
    return (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "logging"
    )


def defines_module_logger(tree: ast.Module, node: ast.AST) -> bool:
    """Defines module logger."""
    if node not in tree.body:
        return False
    if isinstance(node, ast.Assign):
        targets = node.targets
    elif isinstance(node, ast.AnnAssign):
        targets = [node.target]
    else:
        return False

    return any(isinstance(target, ast.Name) and is_logger_name(target.id) for target in targets)


def calls_logger_method(node: ast.AST) -> bool:
    """Calls logger method."""
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return False
    if node.func.attr not in {
        "critical",
        "debug",
        "error",
        "exception",
        "fatal",
        "info",
        "log",
        "warning",
    }:
        return False
    return isinstance(node.func.value, ast.Name) and is_logger_name(node.func.value.id)


def is_logger_name(name: str) -> bool:
    """Return whether logger name."""
    return name in {"LOG", "LOGGER", "logger"}


def node_location(path: Path, node: ast.AST) -> str:
    """Node location."""
    return f"{path.relative_to(ROOT)}:{getattr(node, 'lineno', 0)}"


def is_print_call(node: ast.AST) -> bool:
    """Return whether print call."""
    return (
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print"
    )


def parent_by_child(tree: ast.Module) -> dict[ast.AST, ast.AST]:
    """Parent by child."""
    parents = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def containing_function_name(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str:
    """Containing function name."""
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current.name
    return ""
