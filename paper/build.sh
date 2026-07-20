#!/usr/bin/env bash
#
# Build "Engineering the Channel" and sync the PDF to its published homes.
#
# Portable by design:
#   - Runs from any working directory (resolves its own location, so the
#     relative `fonts/` paths in main.tex always resolve).
#   - Auto-discovers XeLaTeX if it isn't already on PATH (TinyTeX, TeX Live,
#     MacTeX, Homebrew), no machine-specific paths baked into the source.
#   - Writes build artifacts to ./build/ (git-ignored) and copies the final
#     PDF to ../docs/ (committed) and, if present, the sibling website's
#     public/ folder.
#
# Sync rule (2026-07-13): main.tex is the sole source of truth for the paper.
# The website serves hand-maintained renders of the same text:
#   …/website/src/pages/paper.astro   (HTML render)
#   …/website/public/llms-full.txt    (markdown render for LLM ingestion)
# Any revision to main.tex must be applied to every render in the same
# change. This script enforces the rule at the publish moment: if main.tex
# has been edited more recently than any render, the build fails loudly.
# Pass --allow-stale-web to override deliberately (mid-draft iteration);
# the override is explicit, never the silent default.
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

# ── Regenerate the web renders from main.tex (single source of truth) ──
# render.py DERIVES public/llms-full.txt and src/pages/paper.astro from main.tex,
# so the published renders can no longer drift from the paper. This replaces the
# old mtime "sync gate": there is nothing to keep in sync by hand any more. The
# --allow-stale-web flag is now accepted for backward compatibility but is a no-op.
if command -v python3 >/dev/null 2>&1; then
  echo "==> render.py: regenerating web renders from main.tex"
  python3 "$SCRIPT_DIR/render.py" --write
else
  echo "==> WARNING: python3 not found; web renders NOT regenerated (may be stale)" >&2
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
  echo "==> website public/ not found alongside repo; skipped site copy"
fi

echo "Done."
