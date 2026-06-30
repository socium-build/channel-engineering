# Engineering the Channel — LaTeX Source

**"Engineering the Channel: Restoring Software Engineering Discipline in the Age of LLMs"**
Josh Paul · Socium · June 2026

---

## Contents

```
paper/
├── build.sh                  ← One-command build + PDF sync (see below)
├── main.tex                  ← Full LaTeX source (XeLaTeX)
├── socium_logo.png           ← Socium logo (300 dpi PNG, used on cover page)
├── fonts/
│   ├── SourceSerif4-VF.ttf   ← Source Serif 4 variable font (roman, body)
│   ├── SourceSerif4-Italic-VF.ttf  ← Source Serif 4 variable font (italic, body)
│   ├── Inter-SemiBold.otf    ← Inter (headings)
│   ├── Inter-Bold.otf
│   ├── Inter-SemiBoldItalic.otf
│   ├── Inter-BoldItalic.otf
│   ├── Inter-Medium.otf      ← Inter (section labels)
│   └── Inter-MediumItalic.otf
├── build/                    ← Build artifacts (git-ignored)
└── README.md
```

The committed, published PDF lives one level up at
[`../docs/engineering-the-channel.pdf`](../docs/engineering-the-channel.pdf);
`build.sh` regenerates and syncs it.

> **Note:** All figures are drawn natively in `main.tex` — there are no
> external figure files to manage. Figures 1, 2, and 4 are TikZ diagrams
> (the Channel Engineering Architecture, the context-winnowing funnel, and
> the partnership network), and Figure 3 (the Four-Layer Thesis Stack) is a
> stacked-band layout built from the `\layerband` macro. This keeps the
> bundle fully self-contained and the figure typography matched to the
> document fonts.

> **In-text exhibits:** §10 includes a worked-example callout ("A Single Task,
> Traced") built with an `mdframed` box, and each of the nine Practical Principles
> (§9) carries a one-line operational `TEST` rendered by the `\principletest` macro
> (defined near the pull-quote macro in the preamble). Both rely only on the
> already-loaded `mdframed` package and the default monospace font — no new
> dependencies.

---

## Building the PDF

### Requirements

- **TeX Live 2023+** / MacTeX / TinyTeX with **XeLaTeX**
- **No system fonts required.** Both typefaces are bundled in `fonts/` (Source
  Serif 4 for body text, Inter for headings and labels) and loaded by relative
  path, so the document compiles self-contained on macOS, Linux, or Windows.

### Build (recommended)

```bash
./build.sh
```

`build.sh` is location-independent: it `cd`s to its own directory (so the
relative `fonts/` paths resolve no matter where you invoke it), auto-discovers
`xelatex` if it isn't already on `PATH` (TinyTeX, TeX Live, MacTeX, Homebrew),
runs two passes for cross-references, and then syncs the resulting PDF to:

- `../docs/engineering-the-channel.pdf` (the committed, published copy), and
- `../../website/public/engineering-the-channel.pdf` **if** the marketing-site
  repo is checked out as a sibling under `…/socium-build/website` (otherwise it
  skips that copy).

Output: 30 pages.

### Build (manual)

```bash
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex   # run twice for cross-references
```

> No `pip`/Python/matplotlib step is required — the figures are TikZ code
> compiled directly by XeLaTeX. The `tikz` and `pgfplots` packages (both
> loaded in the preamble) ship with any full TeX Live install (or
> `tlmgr install pgf pgfplots`).

---

## Editing Figures

Figures 1, 2, and 4 are `tikzpicture` blocks inside their corresponding
`figure` environments in `main.tex`; Figure 3 is built inline from the
`\layerband` macro (defined just above it). Edit the code in place and
recompile; no external assets are involved. Brand colors are available as the
named LaTeX colors `indigo`, `cyan`, and `midb` (see below).

---

## Font Notes

The `fonts/` directory contains both typefaces (Source Serif 4 for body text,
Inter for headings and labels). All font families in `main.tex` are loaded with
a relative `Path = fonts/`, so the source is self-contained — no system font
installation is required on any platform. Use `./build.sh` (which compiles from
this directory automatically) and the relative paths always resolve; if you run
`xelatex` by hand, do so from this `paper/` directory for the same reason.

---

## Brand Colors

| Role            | Hex       | Used for                              |
|-----------------|-----------|---------------------------------------|
| Indigo          | `#1B1564` | Section underrules, pull quote border, cover rule |
| Cyan            | `#0DB5F1` | Layer 3 highlight, figure accents     |
| Mid-blue        | `#157DCD` | Circuit gradient, figure nodes        |
