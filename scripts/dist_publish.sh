#!/bin/bash
set -euo pipefail

ADDON_NAME="Genehelp"
DISPLAY_NAME="GeneHelp"
DESCRIPTION="Send selected Gramps records to GeneHelp as an online request."
ORIGINAL_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

version_from_branch() {
  local branch="$1"
  git show "$branch:$ADDON_NAME.gpr.py" \
    | sed -n 's/.*version="\([^"]*\)".*/\1/p' \
    | head -n 1
}

VERSION="$(version_from_branch main)"

build_package() {
  local branch="$1"
  local target="$2"
  local expected_target_version="$3"
  local build_root="$TMP_DIR/$target/build"
  local archive_path="$TMP_DIR/$target/$ADDON_NAME.addon.tgz"

  echo "Building $ADDON_NAME $VERSION from $branch for $target"
  mkdir -p "$build_root"

  git archive --format=tar --prefix="$ADDON_NAME/" "$branch" | tar -x -C "$build_root"

  local gpr_file="$build_root/$ADDON_NAME/$ADDON_NAME.gpr.py"
  grep -q "version=\"$VERSION\"" "$gpr_file"
  grep -q "gramps_target_version=\"$expected_target_version\"" "$gpr_file"

  if compgen -G "$build_root/$ADDON_NAME/po/*-local.po" > /dev/null; then
    for po_file in "$build_root/$ADDON_NAME"/po/*-local.po; do
      local lang_code
      lang_code="$(basename "$po_file" -local.po)"
      mkdir -p "$build_root/$ADDON_NAME/locale/$lang_code/LC_MESSAGES"
      msgfmt --output-file="$build_root/$ADDON_NAME/locale/$lang_code/LC_MESSAGES/addon.mo" "$po_file"
    done
  fi

  rm -rf \
    "$build_root/$ADDON_NAME/.git" \
    "$build_root/$ADDON_NAME/.idea" \
    "$build_root/$ADDON_NAME/__pycache__" \
    "$build_root/$ADDON_NAME/.mypy_cache" \
    "$build_root/$ADDON_NAME/.pytest_cache" \
    "$build_root/$ADDON_NAME/.ruff_cache" \
    "$build_root/$ADDON_NAME/data" \
    "$build_root/$ADDON_NAME/dist" \
    "$build_root/$ADDON_NAME/docs" \
    "$build_root/$ADDON_NAME/scripts" \
    "$build_root/$ADDON_NAME/tests" \
    "$build_root/$ADDON_NAME/po" \
    "$build_root/$ADDON_NAME/config.ini" \
    "$build_root/$ADDON_NAME/pyproject.toml" \
    "$build_root/$ADDON_NAME/pylintrc"

  find "$build_root/$ADDON_NAME" -name "__pycache__" -type d -prune -exec rm -rf {} +
  find "$build_root/$ADDON_NAME" -name "*.pyc" -type f -delete
  find "$build_root/$ADDON_NAME" -name "*~" -type f -delete

  tar -czf "$archive_path" -C "$build_root" "$ADDON_NAME"
}

write_listing() {
  local target="$1"
  local expected_target_version="$2"
  local json_path="$TMP_DIR/dist/$target/listings/addons-en.json"

  mkdir -p "$(dirname "$json_path")"
  cat > "$json_path" <<JSON
[
  {
    "n": "$DISPLAY_NAME",
    "i": "$ADDON_NAME",
    "t": 10,
    "d": "$DESCRIPTION",
    "v": "$VERSION",
    "g": "$expected_target_version",
    "s": 2,
    "z": "$ADDON_NAME.addon.tgz"
  }
]
JSON
}

prepare_dist_tree() {
  mkdir -p \
    "$TMP_DIR/dist/gramps60/download" \
    "$TMP_DIR/dist/gramps52/download"

  cp "$TMP_DIR/gramps60/$ADDON_NAME.addon.tgz" \
    "$TMP_DIR/dist/gramps60/download/$ADDON_NAME.addon.tgz"
  cp "$TMP_DIR/gramps52/$ADDON_NAME.addon.tgz" \
    "$TMP_DIR/dist/gramps52/download/$ADDON_NAME.addon.tgz"

  write_listing "gramps60" "6.0"
  write_listing "gramps52" "5.2"

  cat > "$TMP_DIR/dist/.gitignore" <<'EOF'
*
!/.gitignore
!/gramps60/
!/gramps60/download/
!/gramps60/download/Genehelp.addon.tgz
!/gramps60/listings/
!/gramps60/listings/addons-en.json
!/gramps52/
!/gramps52/download/
!/gramps52/download/Genehelp.addon.tgz
!/gramps52/listings/
!/gramps52/listings/addons-en.json
EOF
}

publish_dist_branch() {
  local parent=""
  local tree
  local commit

  GIT_INDEX_FILE="$TMP_DIR/index" git --work-tree="$TMP_DIR/dist" add -A .
  tree="$(GIT_INDEX_FILE="$TMP_DIR/index" git write-tree)"

  if git show-ref --verify --quiet refs/heads/dist; then
    parent="$(git rev-parse refs/heads/dist)"
    if [[ "$tree" == "$(git rev-parse "$parent^{tree}")" ]]; then
      echo "No dist changes to commit."
      return
    fi
    commit="$(printf "Update %s addon to version %s for all supported versions\n" "$DISPLAY_NAME" "$VERSION" \
      | git commit-tree "$tree" -p "$parent")"
  else
    commit="$(printf "Publish %s addon version %s for all supported versions\n" "$DISPLAY_NAME" "$VERSION" \
      | git commit-tree "$tree")"
  fi

  git update-ref refs/heads/dist "$commit"
  git push origin dist
}

if [[ "$ORIGINAL_BRANCH" != "main" ]]; then
  echo "Run this script from main. Current branch: $ORIGINAL_BRANCH" >&2
  exit 1
fi

if [[ -n "$(git status --short --untracked-files=no)" ]]; then
  echo "Tracked working tree changes exist. Commit or stash them before publishing dist." >&2
  exit 1
fi

if [[ -z "$VERSION" ]]; then
  echo "Could not extract $ADDON_NAME version from main." >&2
  exit 1
fi

if [[ "$(version_from_branch 5.2)" != "$VERSION" ]]; then
  echo "Version mismatch between main and 5.2." >&2
  exit 1
fi

build_package "main" "gramps60" "6.0"
build_package "5.2" "gramps52" "5.2"
prepare_dist_tree
publish_dist_branch

echo "Published $DISPLAY_NAME $VERSION to dist."
