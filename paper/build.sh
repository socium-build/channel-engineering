#!/usr/bin/env bash
#
# Build "Engineering the Channel" and sync the PDF to its published homes.
#
# Portable by design:
#   - Runs from any working directory (resolves its own location, so the
#     relative `fonts/` paths in main.tex always resolve).
#   - Auto-discovers XeLaTeX if it isn't already on PATH (TinyTeX, TeX Live,
#     MacTeX, Homebrew) — no machine-specific paths baked into the source.
#   - Writes build artifacts to ./build/ (git-ignored) and copies the final
#     PDF to ../docs/ (committed) and, if present, the sibling website's
#     public/ folder.
#
# Sync rule (2026-07-13): main.tex is the sole source of truth for the paper.
# The website serves a hand-maintained HTML render of the same text
# (…/website/src/pages/paper.astro). Any revision to main.tex must be applied
# to paper.astro in the same change. This script enforces the rule at the
# publish moment: if main.tex has been edited more recently than paper.astro,
# the build fails loudly. Pass --allow-stale-web to override deliberately
# (mid-draft iteration); the override is explicit, never the silent default.
#
# Usage:  ./build.sh [--allow-stale-web]
#
set -euo pipefail

ALLOW_STALE_WEB=0
for arg in "$@"; do
  case "$arg" in
    --allow-stale-web) ALLOW_STALE_WEB=1 ;;
    *) echo "error: unknown argument '$arg' (usage: ./build.sh [--allow-stale-web])" >&2; exit 1 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Web render sync gate (see header: sync rule) ────────────
# Heuristic: file mtimes on the working tree — honest for a single
# maintainer on one machine ("which did I edit last"), cheap, and free of
# git-state edge cases (paper.astro may be uncommitted while being written).
mtime() { stat -f %m "$1" 2>/dev/null || stat -c %Y "$1" 2>/dev/null; }

WEB_ASTRO="$SCRIPT_DIR/../../website/src/pages/paper.astro"
if [ -f "$WEB_ASTRO" ]; then
  TEX_T="$(mtime "$SCRIPT_DIR/main.tex")"
  WEB_T="$(mtime "$WEB_ASTRO")"
  if [ "$TEX_T" -gt "$WEB_T" ]; then
    if [ "$ALLOW_STALE_WEB" -eq 1 ]; then
      echo "==> WARNING: main.tex is newer than the website HTML render (override accepted)."
    else
      echo "" >&2
      echo "error: main.tex is newer than the website HTML render." >&2
      echo "       main.tex is the sole source of truth; apply the same revision to" >&2
      echo "       $WEB_ASTRO" >&2
      echo "       in the same change, then rebuild. To build anyway (mid-draft" >&2
      echo "       iteration), pass --allow-stale-web explicitly." >&2
      exit 1
    fi
  else
    echo "==> web render sync: paper.astro is current (or newer) — ok"
  fi
elif [ -d "$SCRIPT_DIR/../../website" ]; then
  echo "error: website checkout found but src/pages/paper.astro is missing." >&2
  echo "       The HTML render is a published surface; restore it or pass --allow-stale-web." >&2
  [ "$ALLOW_STALE_WEB" -eq 1 ] || exit 1
else
  echo "==> website repo not checked out alongside — web sync gate skipped"
fi

# ── Locate xelatex ──────────────────────────────────────────
if ! command -v xelatex >/dev/null 2>&1; then
  for cand in \
    "$HOME/Library/TinyTeX/bin/universal-darwin" \
    "$HOME/.TinyTeX/bin/universal-darwin" \
    "/Library/TeX/texbin" \
    /usr/local/texlive/*/bin/* \
    /opt/homebrew/bin \
    /usr/local/bin; do
    if [ -x "$cand/xelatex" ]; then
      PATH="$cand:$PATH"
      break
    fi
  done
fi

if ! command -v xelatex >/dev/null 2>&1; then
  echo "error: xelatex not found." >&2
  echo "       Install TeX Live / MacTeX / TinyTeX, or add xelatex to PATH." >&2
  exit 1
fi

# ── Compile (two passes for cross-references and the TOC) ───
BUILD_DIR="$SCRIPT_DIR/build"
mkdir -p "$BUILD_DIR"

echo "==> xelatex (pass 1/2)"
xelatex -interaction=nonstopmode -halt-on-error -output-directory="$BUILD_DIR" main.tex >/dev/null
echo "==> xelatex (pass 2/2)"
xelatex -interaction=nonstopmode -halt-on-error -output-directory="$BUILD_DIR" main.tex >/dev/null

PDF="$BUILD_DIR/main.pdf"
[ -f "$PDF" ] || { echo "error: build produced no PDF (see $BUILD_DIR/main.log)" >&2; exit 1; }

if command -v pdfinfo >/dev/null 2>&1; then
  echo "==> built $(pdfinfo "$PDF" | awk '/^Pages:/{print $2}') pages"
fi

# ── Sync canonical copies ───────────────────────────────────
DOCS_PDF="$SCRIPT_DIR/../docs/engineering-the-channel.pdf"
mkdir -p "$(dirname "$DOCS_PDF")"
cp "$PDF" "$DOCS_PDF"
echo "==> synced -> ${DOCS_PDF}"

# The marketing site is a separate repo; copy only if it's checked out as a
# sibling under the same org tree (…/socium-build/website).
WEBSITE_PDF="$SCRIPT_DIR/../../website/public/engineering-the-channel.pdf"
if [ -d "$(dirname "$WEBSITE_PDF")" ]; then
  cp "$PDF" "$WEBSITE_PDF"
  echo "==> synced -> ${WEBSITE_PDF}"
else
  echo "==> website public/ not found alongside repo — skipped site copy"
fi

echo "Done."
