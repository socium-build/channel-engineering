#!/usr/bin/env python3
r"""
render.py — derive the web renders of "Engineering the Channel" from main.tex.

main.tex is the single source of truth. This script regenerates the prose body of
the two published renders so they can never silently drift from the paper again:

  - public/llms-full.txt   (Markdown, machine ingestion)
  - src/pages/paper.astro  (Astro HTML page)

Non-body scaffolding that lives only in the renders (the Astro frontmatter/JSON-LD,
the site header + TOC, the four hand-authored SVG <figure> blocks, the traced-task
box, and the closing download/footer/style) is treated as a TEMPLATE: it is lifted
verbatim from the current render files and re-emitted unchanged. Only the prose,
headings, footnotes/Notes, References, and TOC list are derived from main.tex.

Standard library only. Emits *.generated files for review; it does NOT overwrite
the live renders. Verify a generated file against main.tex / the compiled PDF, then
promote it (mv) once satisfied.

Known faithful-to-source deltas vs. the current hand-maintained renders (by design):
  * llms figure captions become the terse main.tex \caption text (the hand-written
    SVG descriptions in the old llms file are not in the source).
  * llms Note URLs are appended at the end of each note (single-URL notes match the
    old file exactly; multi-URL notes differ from the old hand interleaving).
  * Reference link text is main.tex's href display arg (some old astro refs were
    hand-shortened).
  * em-dash spacing follows the source ("X---Y" -> "X—Y", no surrounding spaces).
  * The traced-task box (§10) is preserved verbatim from the current renders, not
    derived (too intricate to re-derive safely in one pass); flagged in the report.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN_TEX = os.path.join(HERE, "main.tex")
WEB = os.path.normpath(os.path.join(HERE, "..", "..", "website"))
LLMS = os.path.join(WEB, "public", "llms-full.txt")
ASTRO = os.path.join(WEB, "src", "pages", "paper.astro")

# section slugs, in document order (main.tex \section order)
SLUGS = [
    "reliability-problem",
    "channel-as-communication-system",
    "executive-control",
    "beyond-context-engineering",
    "historical-precedents",
    "abandonment-of-discipline",
    "probability-space",
    "validation-gate",
    "four-layer-thesis",
    "socium-model",
    "related-work",
    "conclusion",
]

SENT = "\x00"  # sentinel delimiter


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def braced(s, i):
    """s[i] == '{'; return (inner, index_after_closing_brace)."""
    assert s[i] == "{", repr(s[i:i + 20])
    depth = 0
    j = i
    n = len(s)
    while j < n:
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    raise ValueError("unbalanced braces at %d" % i)


def extract_cmd(s, cmd, tag, store):
    """Replace every \\cmd{...} with a sentinel token, storing the inner LaTeX."""
    needle = "\\" + cmd + "{"
    out = []
    i = 0
    while True:
        k = s.find(needle, i)
        if k < 0:
            out.append(s[i:])
            break
        out.append(s[i:k])
        inner, end = braced(s, k + len(needle) - 1)
        idx = len(store)
        store.append(inner)
        out.append("%s%s%d%s" % (SENT, tag, idx, SENT))
        i = end
    return "".join(out)


def conv(s, mode, urls=None):
    """Convert an inline LaTeX fragment.

    mode: 'md'   -> markdown (emphasis kept as * / **, href -> plain text)
          'html' -> HTML (emphasis -> <em>/<strong>, href -> <a>)
          'plain'-> plain text (emphasis stripped, href -> text; urls collected)
    """
    out = []
    i = 0
    n = len(s)

    def esc(ch):
        if mode == "html":
            if ch == "&":
                return "&amp;"
            if ch == "<":
                return "&lt;"
            if ch == ">":
                return "&gt;"
        return ch

    def wrap(cmd, inner):
        if mode == "plain":
            return inner
        if cmd == "textbf":
            return ("**%s**" % inner) if mode == "md" else ("<strong>%s</strong>" % inner)
        if cmd == "texttt":
            return ("`%s`" % inner) if mode == "md" else ("<code>%s</code>" % inner)
        # emph / textit
        return ("*%s*" % inner) if mode == "md" else ("<em>%s</em>" % inner)

    while i < n:
        c = s[i]

        # sentinel tokens pass through untouched
        if c == SENT:
            j = s.find(SENT, i + 1)
            out.append(s[i:j + 1])
            i = j + 1
            continue

        if c == "\\":
            # \href{url}{text}
            if s.startswith("\\href{", i):
                url, a = braced(s, i + 5)
                txt, b = braced(s, a)
                tconv = conv(txt, mode, urls)
                if mode == "html":
                    out.append('<a href="%s">%s</a>' % (url, tconv))
                else:
                    out.append(tconv)
                    if urls is not None:
                        urls.append(url)
                i = b
                continue
            handled = False
            for cmd in ("emph", "textit", "textbf", "texttt"):
                pre = "\\" + cmd + "{"
                if s.startswith(pre, i):
                    inner, b = braced(s, i + len(pre) - 1)
                    out.append(wrap(cmd, conv(inner, mode, urls)))
                    i = b
                    handled = True
                    break
            if handled:
                continue
            # escaped literals
            if i + 1 < n and s[i + 1] in "%$&_#{}":
                out.append(esc(s[i + 1]))
                i += 2
                continue
            # thin spaces / explicit spacing
            if i + 1 < n and s[i + 1] in ",;:! ":
                out.append(" ")
                i += 2
                continue
            m = re.match(r"\\[a-zA-Z]+", s[i:])
            if m:
                word = m.group(0)[1:]
                repl = {
                    "ldots": "…",
                    "textasciitilde": "~",
                    "enspace": " ", "quad": " ", "qquad": " ",
                    "textperiodcentered": "·",
                    "rightarrow": "→",
                }.get(word, "")
                out.append(repl)
                i += m.end()
                # swallow one following space that LaTeX would eat after a control word
                if i < n and s[i] == " ":
                    i += 1
                continue
            out.append(esc(c))
            i += 1
            continue

        # inline math
        if c == "$":
            j = s.find("$", i + 1)
            inner = s[i + 1:j]
            inner = inner.replace("\\approx", " ≈ ")
            inner = re.sub(r"\^\{(\w+)\}", r"^\1", inner)
            inner = inner.replace("{", "").replace("}", "")
            inner = re.sub(r"\s+", " ", inner).strip()
            out.append(inner)
            i = j + 1
            continue

        # multi-char punctuation
        if s.startswith("---", i):
            out.append("—")
            i += 3
            continue
        if s.startswith("--", i):
            out.append("–")
            i += 2
            continue
        if s.startswith("``", i):
            out.append('"')
            i += 2
            continue
        if s.startswith("''", i):
            out.append('"')
            i += 2
            continue
        if c == "`":
            out.append("'")
            i += 1
            continue
        if c == "~":
            out.append(" ")
            i += 1
            continue
        if c in "{}":
            # bare LaTeX grouping brace in prose (e.g. the 4{,}867 comma idiom):
            # carries no output meaning; drop it. Escaped braces (\{ \}) are handled
            # above and kept as literals.
            i += 1
            continue
        out.append(esc(c))
        i += 1

    return re.sub(r"[ \t]+", " ", "".join(out))


def load_body():
    tex = read(MAIN_TEX)
    a = tex.index("\\section*{Abstract}")
    b = tex.index("\\end{document}")
    return tex[a:b]


def build():
    body = load_body()

    footnotes, pullquotes, tests = [], [], []
    body = extract_cmd(body, "footnote", "F", footnotes)
    body = extract_cmd(body, "pullquote", "Q", pullquotes)
    body = extract_cmd(body, "principletest", "T", tests)

    # figures (three \begin{figure} envs + the layerband Figure 3), numbered by
    # document position.
    fig_caption = {}
    spans = []
    for m in re.finditer(r"\\begin\{figure\}.*?\\caption\{([^{}]*)\}.*?\\end\{figure\}", body, re.DOTALL):
        spans.append((m.start(), m.end(), m.group(1)))
    m3 = re.search(r"\\smallskip\s*\n\s*% Figure 3 .*?Figure 3:\s*(.*?)\}\s*\n", body, re.DOTALL)
    if m3:
        spans.append((m3.start(), m3.end(), m3.group(1)))
    spans.sort()
    for idx in range(len(spans) - 1, -1, -1):
        st, en, cap = spans[idx]
        num = idx + 1
        fig_caption[num] = re.sub(r"\s+", " ", cap).strip()
        body = body[:st] + "\n%sG%d%s\n" % (SENT, num, SENT) + body[en:]

    # traced-task mdframed
    body = re.sub(r"\\begin\{mdframed\}.*?\\end\{mdframed\}", "\n%sTRACE%s\n" % (SENT, SENT),
                  body, flags=re.DOTALL)

    # split off references + author (starred sections, not numbered / handled apart)
    r_idx = body.index("\\section*{References}")
    a_idx = body.index("\\section*{About the Author}")
    pre = body[:r_idx]
    ref_region = body[r_idx:a_idx]
    author_region = body[a_idx:]

    blocks = build_blocks(pre)
    refs = parse_references(ref_region)
    author = parse_author(author_region)

    return blocks, footnotes, pullquotes, tests, fig_caption, refs, author


def build_blocks(pre):
    blocks = []
    buf = []
    seccount = [0]

    SKIP_EXACT = {
        "\\newpage", "\\bigskip", "\\smallskip", "\\medskip",
        "\\normalsize", "\\footnotesize", "\\sloppy", "\\noindent",
    }

    def flush():
        text = " ".join(buf).strip()
        buf.clear()
        if text:
            blocks.append(("p", text))

    for raw in pre.split("\n"):
        s = raw.strip()
        if s == "":
            flush()
            continue
        if s.startswith("%"):
            continue
        if s in SKIP_EXACT:
            continue
        if s.startswith("\\setcounter") or s.startswith("\\setlength") or \
           s.startswith("\\interlinepenalty") or s.startswith("\\newcommand"):
            continue
        if s.startswith("\\section*{Abstract}"):
            flush()
            blocks.append(("abstract",))
            continue
        m = re.match(r"\\section\{(.*)\}\s*$", s)
        if m:
            flush()
            seccount[0] += 1
            blocks.append(("h2", seccount[0], m.group(1)))
            continue
        m = re.match(r"\\section\*\{(.*)\}\s*$", s)
        if m:
            flush()
            blocks.append(("h2u", m.group(1)))  # unnumbered back-matter heading
            continue
        m = re.match(r"\\subsection\*?\{(.*)\}\s*$", s)
        if m:
            flush()
            blocks.append(("h3", m.group(1)))
            continue
        buf.append(raw.strip())
    flush()
    return blocks


def parse_references(region):
    region = region.split("\\section*{References}", 1)[1]
    refs = []
    # Text before the first entry (an \\textit{...} note) is otherwise dropped;
    # carry it as a sentinel so both renders show it, not just the PDF.
    head_region = region.split("\\noindent\\textbf{", 1)[0]
    lead = re.search(r"\\textit\{([^{}]*)\}", head_region)
    if lead:
        refs.append(("__LEAD__", re.sub(r"\s+", " ", lead.group(1)).strip(), None))
    for chunk in region.split("\\noindent\\textbf{")[1:]:
        cite_part = chunk.split("\\\\*", 1)
        head = cite_part[0]
        m = re.match(r"\s*\d+\.\}\\enspace\s*(.*)$", head, re.DOTALL)
        citation = m.group(1).strip() if m else head.strip()
        citation = citation.rstrip()
        url = disp = None
        if len(cite_part) > 1:
            mu = re.search(r"\\href\{([^}]*)\}\{(.*?)\}\}", cite_part[1], re.DOTALL)
            if mu:
                url, disp = mu.group(1), mu.group(2)
        refs.append((citation, url, disp))
    return refs


def parse_author(region):
    region = region.split("\\section*{About the Author}", 1)[1]
    region = region.replace("\\noindent", " ")
    # Drop spacing commands with their braced argument (e.g. \\vspace{0.9em}),
    # which double as the paragraph separators in this section.
    region = re.sub(r"\\vspace\*?\{[^{}]*\}", "\n\n", region)
    # Preserve paragraph breaks; flatten only the wrapping inside each paragraph.
    paras = [" ".join(x.split()) for x in re.split(r"\n\s*\n", region) if x.strip()]
    return "\n\n".join(paras).strip()


# ---- footnote / Notes rendering ------------------------------------------------

def note_md(latex):
    urls = []
    txt = conv(latex, "plain", urls).strip()
    txt = re.sub(r"\s+", " ", txt)
    extra = [u for u in urls if u not in txt]
    if extra:
        txt = txt + " " + " ".join(extra)
    return txt


def note_html(latex):
    txt = conv(latex, "html").strip()
    return re.sub(r"\s+", " ", txt)


def sub_footnote_markers(text, mode):
    def rep(m):
        n = int(m.group(1)) + 1
        if mode == "md":
            return "[%d]" % n
        return '<sup class="fn" id="fnref-%d"><a href="#fn-%d">%d</a></sup>' % (n, n, n)
    return re.sub(SENT + r"F(\d+)" + SENT, rep, text)


# ---- markdown emission ---------------------------------------------------------

def emit_llms(blocks, footnotes, pullquotes, tests, fig_caption, refs, author):
    cur_llms = read(LLMS)
    header = cur_llms[:cur_llms.index("## Abstract")]
    footer = cur_llms[cur_llms.rindex("---"):]
    ti = cur_llms.index("A single task, traced:")
    trace_block = cur_llms[ti:cur_llms.index("\n## ", ti)].rstrip()

    out = [header.rstrip("\n")]
    parts = []

    def para(text):
        return sub_footnote_markers(conv(text, "md"), "md").strip()

    for blk in blocks:
        k = blk[0]
        if k == "abstract":
            parts.append("## Abstract")
        elif k == "h2":
            parts.append("## %d %s" % (blk[1], conv(blk[2], "md").strip()))
        elif k == "h2u":
            parts.append("## %s" % conv(blk[1], "md").strip())
        elif k == "h3":
            parts.append("### " + conv(blk[1], "md").strip())
        elif k == "p":
            t = blk[1]
            mp = re.fullmatch(SENT + r"Q(\d+)" + SENT, t)
            mt = re.fullmatch(SENT + r"T(\d+)" + SENT, t)
            mg = re.fullmatch(SENT + r"G(\d+)" + SENT, t)
            if t == SENT + "TRACE" + SENT:
                parts.append(trace_block)
            elif mp:
                q = conv(pullquotes[int(mp.group(1))], "md").strip()
                # Every line needs the marker: a bare continuation line ends the
                # blockquote and splits the sentence into a second paragraph.
                parts.append("\n".join("> " + ln.strip() for ln in q.splitlines()))
            elif mt:
                parts.append("TEST: " + conv(tests[int(mt.group(1))], "md").strip())
            elif mg:
                num = int(mg.group(1))
                parts.append("[Figure %d. %s]" % (num, conv(fig_caption[num], "md").strip()))
            else:
                parts.append(para(t))

    out.append("\n\n".join(parts))

    notes = ["## Notes", ""]
    for idx, fn in enumerate(footnotes):
        notes.append("%d. %s" % (idx + 1, note_md(fn)))
    out.append("\n".join(notes))

    references = ["## References", ""]
    n = 0
    for citation, url, disp in refs:
        if citation == "__LEAD__":
            references.append("*%s*" % conv(url, "md").strip())
            references.append("")
            continue
        n += 1
        line = "%d. %s" % (n, re.sub(r"\s+", " ", conv(citation, "md").strip()))
        if url and url not in line:
            line = line + " " + url
        references.append(line)
    out.append("\n".join(references))

    out.append("## About the Author\n\n" + conv(author, "md").strip())
    out.append(footer.rstrip("\n") + "\n")

    return "\n\n".join(out)


# ---- astro emission ------------------------------------------------------------

def emit_astro(blocks, footnotes, pullquotes, tests, fig_caption, refs, author):
    src = read(ASTRO)
    prefix = src[:src.index('      <nav class="paper-toc"')]
    suffix = src[src.index('      <section class="paper-section download-section">'):]

    figures = re.findall(r'        <figure class="fig[^"]*">.*?</figure>', src, re.DOTALL)
    assert len(figures) == 4, "expected 4 figures, found %d" % len(figures)
    trace = re.search(r'        <aside class="trace-box">.*?</aside>', src, re.DOTALL).group(0)

    # section titles for the TOC (numbered)
    sec_titles = []
    for blk in blocks:
        if blk[0] == "h2":
            sec_titles.append((blk[1], conv(blk[2], "html").strip()))

    # ---- TOC ----
    toc = ['      <nav class="paper-toc" aria-label="Contents">',
           '        <h2>Contents</h2>', '        <ul>',
           '          <li><a href="#abstract">Abstract</a></li>']
    for num, title in sec_titles:
        slug = SLUGS[num - 1]
        toc.append('          <li><a href="#%s"><span class="secnum">%d</span> %s</a></li>'
                    % (slug, num, title))
    toc.append('          <li><a href="#notes">Notes</a></li>')
    toc.append('          <li><a href="#references">References</a></li>')
    toc.append('          <li><a href="#about-the-author">About the Author</a></li>')
    toc.append('        </ul>')
    toc.append('      </nav>')

    # ---- body sections ----
    body = []
    open_section = False

    def close():
        nonlocal open_section
        if open_section:
            body.append("      </section>")
            open_section = False

    def para(text):
        return sub_footnote_markers(conv(text, "html"), "html").strip()

    for blk in blocks:
        k = blk[0]
        if k == "abstract":
            close()
            body.append('      <section id="abstract" class="paper-section">')
            body.append("        <h2>Abstract</h2>")
            open_section = True
        elif k == "h2":
            close()
            slug = SLUGS[blk[1] - 1]
            body.append('      <section id="%s" class="paper-section">' % slug)
            body.append('        <h2><span class="secnum">%d</span> %s</h2>'
                        % (blk[1], conv(blk[2], "html").strip()))
            open_section = True
        elif k == "h2u":
            close()
            slug = re.sub(r"[^a-z0-9]+", "-", blk[1].lower()).strip("-")
            body.append('      <section id="%s" class="paper-section">' % slug)
            body.append("        <h2>%s</h2>" % conv(blk[1], "html").strip())
            open_section = True
        elif k == "h3":
            body.append("        <h3>%s</h3>" % conv(blk[1], "html").strip())
        elif k == "p":
            t = blk[1]
            mp = re.fullmatch(SENT + r"Q(\d+)" + SENT, t)
            mt = re.fullmatch(SENT + r"T(\d+)" + SENT, t)
            mg = re.fullmatch(SENT + r"G(\d+)" + SENT, t)
            if t == SENT + "TRACE" + SENT:
                body.append(trace)
            elif mp:
                body.append('        <blockquote class="pull-quote"><p>%s</p></blockquote>'
                            % conv(pullquotes[int(mp.group(1))], "html").strip())
            elif mt:
                body.append('        <div class="principle-test"><span class="test-label">Test</span><p>%s</p></div>'
                            % conv(tests[int(mt.group(1))], "html").strip())
            elif mg:
                body.append(figures[int(mg.group(1)) - 1])
            else:
                body.append("        <p>%s</p>" % para(t))
    close()

    # ---- Notes ----
    notes = ['      <section id="notes" class="paper-section">',
             '        <h2>Notes</h2>', '        <ol class="notes-list">']
    for idx, fn in enumerate(footnotes):
        n = idx + 1
        notes.append('          <li id="fn-%d">%s <a class="fn-back" href="#fnref-%d" aria-label="Back to text">↩</a></li>'
                     % (n, note_html(fn), n))
    notes.append("        </ol>")
    notes.append("      </section>")

    # ---- References ----
    ref_lead = next((u for c, u, _ in refs if c == "__LEAD__"), None)
    references = ['      <section id="references" class="paper-section">',
                  '        <h2>References</h2>']
    if ref_lead:
        references.append('        <p class="refs-note">%s</p>' % conv(ref_lead, "html").strip())
    references.append('        <ol class="refs">')
    for citation, url, disp in refs:
        if citation == "__LEAD__":
            continue
        cite_html = conv(citation, "html").strip().rstrip()
        if url:
            references.append("          <li>%s<br /><a href=\"%s\">%s</a></li>"
                              % (cite_html, url, conv(disp, "html").strip()))
        else:
            references.append("          <li>%s</li>" % cite_html)
    references.append("        </ol>")
    references.append("      </section>")

    # ---- Author ----
    author_html = ['      <section id="about-the-author" class="paper-section">',
                   "        <h2>About the Author</h2>",
                   "        <p>%s</p>" % conv(author, "html").strip(),
                   "      </section>"]

    middle = "\n".join(toc) + "\n\n" + "\n".join(body) + "\n\n" + \
        "\n".join(notes) + "\n\n" + "\n".join(references) + "\n\n" + \
        "\n".join(author_html) + "\n\n"
    return prefix + middle + suffix


# ---- parity check ---------------------------------------------------------------

def verify_parity(md, astro, footnotes, refs):
    """Both renders come from one source, and nothing was checking they agreed.

    That is how 54 references went missing from llms-full.txt while the HTML had
    them all, in a file the site advertises as carrying "notes and references".
    Counts and headings only: comparing prose across two markup languages is a
    normalizer rabbit hole, and a count mismatch is what the real failure looks
    like anyway.
    """
    problems = []

    md_secs = re.findall(r"^##\s+(\d+\s.+)$", md, re.M)
    ht_secs = [re.sub(r"<[^>]+>", "", m) for m in
               re.findall(r"<h2><span class=\"secnum\">(.*?)</h2>", astro, re.S)]
    if len(md_secs) != len(ht_secs):
        problems.append("sections: md=%d html=%d" % (len(md_secs), len(ht_secs)))
    else:
        for a, b in zip(md_secs, ht_secs):
            if re.sub(r"\s+", " ", a).strip() != re.sub(r"\s+", " ", b).strip():
                problems.append("section title differs: %r vs %r" % (a, b))

    pairs = [
        ("footnotes", len(re.findall(r"<li id=\"fn-\d+\">", astro)), len(footnotes)),
        ("references", len(re.findall(r"^\d+\.\s", md[md.find("## References"):
                                                     md.find("## About the Author")], re.M)),
         len([r for r in refs if r[0] != "__LEAD__"])),
        ("pullquotes", len(re.findall(r"<blockquote class=\"pull-quote\">", astro)),
         len(re.findall(r"(?:^>.*\n?)+", md, re.M))),
    ]
    for name, a, b in pairs:
        if a != b:
            problems.append("%s: html/source=%d md=%d" % (name, a, b))

    md_notes = len(re.findall(r"^\d+\.\s", md[md.find("## Notes"):md.find("## References")], re.M))
    if md_notes != len(footnotes):
        problems.append("notes in md=%d, source footnotes=%d" % (md_notes, len(footnotes)))

    return problems


def main():
    blocks, footnotes, pullquotes, tests, fig_caption, refs, author = build()

    llms_out = emit_llms(blocks, footnotes, pullquotes, tests, fig_caption, refs, author)
    astro_out = emit_astro(blocks, footnotes, pullquotes, tests, fig_caption, refs, author)

    promote = "--write" in sys.argv
    llms_path = LLMS if promote else LLMS + ".generated"
    astro_path = ASTRO if promote else ASTRO + ".generated"

    with open(llms_path, "w", encoding="utf-8") as f:
        f.write(llms_out)
    with open(astro_path, "w", encoding="utf-8") as f:
        f.write(astro_out)

    print("wrote %s (%d footnotes, %d refs)" % (llms_path, len(footnotes), len([r for r in refs if r[0] != "__LEAD__"])))

    problems = verify_parity(llms_out, astro_out, footnotes, refs)
    if problems:
        print("PARITY CHECK FAILED: the two renders disagree", file=sys.stderr)
        for msg in problems:
            print("  - %s" % msg, file=sys.stderr)
        return 1
    print("wrote %s" % astro_path)
    print("parity ok: sections, notes, references, and pull quotes match across renders")
    return 0


if __name__ == "__main__":
    raise SystemExit(main() or 0)
