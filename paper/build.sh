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
# Usage:  ./build.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

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
