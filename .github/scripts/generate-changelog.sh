#!/usr/bin/env bash
set -euo pipefail

PREV_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)

if [ -z "$PREV_TAG" ] && [ -f "patches-bundle.json" ]; then
    PREV_TAG=$(grep -E '"version"' patches-bundle.json | head -n1 | sed -E 's/.*"v?([0-9]+\.[0-9]+\.[0-9]+)".*/v\1/')
fi
PREV_TAG="${PREV_TAG:-v3.75.0}"

BASE_VER="${PREV_TAG#v}"
IFS='.' read -r MAJOR MINOR PATCH <<< "$BASE_VER"

if git rev-parse "$PREV_TAG" >/dev/null 2>&1; then
    LOG_RANGE="${PREV_TAG}..HEAD"
else
    LOG_RANGE="HEAD"
fi

COMMITS=$(git log "$LOG_RANGE" --pretty=format:"* %s (%h) by @%an" --no-merges 2>/dev/null | grep -v "chore(release)" || true)

SEMANTIC_BUMP="false"
if echo "$COMMITS" | grep -qE '^\* feat(\([^)]+\))?!?:'; then
    MINOR=$((MINOR + 1))
    PATCH=0
    SEMANTIC_BUMP="true"
elif echo "$COMMITS" | grep -qE '^\* (fix|perf|refactor)(\([^)]+\))?:'; then
    PATCH=$((PATCH + 1))
    SEMANTIC_BUMP="true"
elif [ "${FORCE_PATCH:-false}" = "true" ]; then
    PATCH=$((PATCH + 1))
    SEMANTIC_BUMP="true"
fi

NEW_VERSION="v${MAJOR}.${MINOR}.${PATCH}"

echo "## What's Changed"
echo ""
if [ -n "$COMMITS" ]; then
    echo "$COMMITS"
else
    echo "* Build localized Piko NewX patch bundle."
fi
echo ""
echo "**Full Changelog**: https://github.com/${GITHUB_REPOSITORY:-crimera/piko-newx}/compare/${PREV_TAG}...${NEW_VERSION}"

echo "$NEW_VERSION" >&2
echo "semantic_bump=$SEMANTIC_BUMP" >&2
