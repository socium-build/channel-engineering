#!/usr/bin/env python3
"""Verify the machine ingested the plan the human approved.

Approval is not the last step before execution; ingestion is. A human approves a
markdown spec. The system then parses it into what it will actually run. If those
two things differ, no output gate can catch it, because the divergence happened on
the way *in*: the model is faithfully executing a plan nobody approved.

So the parse reports itself. This script reads a spec, prints the manifest it
derived (phases and tasks, by name and count), and **refuses loudly** rather than
guessing on anything unknown, duplicated, or incomplete. A human confirms the
manifest matches what they signed off on, and only then does execution start.

Zero dependencies; Python 3.8+ standard library only.

Usage:
    python3 ingest.py spec.example.md
    python3 ingest.py spec.broken.md

Exit code 0 = parsed cleanly, 1 = refused (reasons printed), 2 = bad invocation.
"""
from __future__ import annotations

import re
import sys

TASK_RE = re.compile(r"^###\s+Task\s+(\d+)\.(\d+)\s*:\s*(.+?)\s*$")
SECTION_RE = re.compile(r"^\*\*(.+?)\*\*")
CRITERION_RE = re.compile(r"^\s*-\s+\[[ xX]\]\s+(.+?)\s*$")
BULLET_RE = re.compile(r"^\s*-\s+(?!\[[ xX]\])(.+?)\s*$")

# Headings allowed at the '###' level inside the Tasks section. Anything else is
# a parse the human did not approve, so we stop instead of skipping it.
KNOWN_TASK_SECTIONS = {"Acceptance criteria", "Evidence to submit", "Gate"}


class Task:
    def __init__(self, phase: int, number: int, title: str, line: int):
        self.phase = phase
        self.number = number
        self.title = title
        self.line = line
        self.criteria: list[str] = []
        self.evidence: list[str] = []
        self.sections: list[str] = []

    @property
    def ident(self) -> str:
        return f"{self.phase}.{self.number}"


def parse(text: str) -> "tuple[list[Task], list[str]]":
    """Return (tasks, refusals). A non-empty refusal list means: do not execute."""
    tasks: list[Task] = []
    refusals: list[str] = []
    current: "Task | None" = None
    bucket: "str | None" = None
    in_tasks = False

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()

        if line.startswith("## "):
            in_tasks = line[3:].strip().lower() == "tasks"
            current, bucket = None, None
            continue

        if line.startswith("### "):
            if not in_tasks:
                continue
            m = TASK_RE.match(line)
            if not m:
                refusals.append(
                    f"line {lineno}: heading in Tasks is not a task I can parse: {line!r}"
                )
                current, bucket = None, None
                continue
            current = Task(int(m.group(1)), int(m.group(2)), m.group(3), lineno)
            tasks.append(current)
            bucket = None
            continue

        if current is None:
            continue

        m = SECTION_RE.match(line)
        if m:
            name = m.group(1).split("(")[0].strip().rstrip(":")
            current.sections.append(name)
            if name not in KNOWN_TASK_SECTIONS:
                refusals.append(
                    f"line {lineno}: task {current.ident} has an unrecognized section "
                    f"{name!r}; refusing rather than ignoring it"
                )
                bucket = None
            else:
                bucket = name
            continue

        if bucket == "Acceptance criteria":
            cm = CRITERION_RE.match(line)
            if cm:
                current.criteria.append(cm.group(1))
        elif bucket == "Evidence to submit":
            bm = BULLET_RE.match(line)
            if bm:
                current.evidence.append(bm.group(1))

    # Structural refusals, evaluated over the whole parse.
    if not tasks:
        refusals.append("no tasks found; a spec with nothing to execute is not a plan")

    seen: dict = {}
    for t in tasks:
        if t.ident in seen:
            refusals.append(
                f"duplicate task {t.ident} (lines {seen[t.ident]} and {t.line}); "
                f"ambiguous which one to run"
            )
        else:
            seen[t.ident] = t.line
        if not t.criteria:
            refusals.append(
                f"task {t.ident} has no checkable acceptance criteria; "
                f"it is a prompt, not a task"
            )
        if not t.evidence:
            refusals.append(f"task {t.ident} names no evidence for a gate to validate")

    return tasks, refusals


def print_manifest(tasks: "list[Task]") -> None:
    phases: dict = {}
    for t in tasks:
        phases.setdefault(t.phase, []).append(t)

    print("INGESTED PLAN")
    print(f"  phases: {len(phases)}   tasks: {len(tasks)}")
    for phase in sorted(phases):
        items = phases[phase]
        print(f"\n  Phase {phase}  ({len(items)} task{'s' if len(items) != 1 else ''})")
        for t in items:
            print(f"    {t.ident}  {t.title}")
            print(f"          {len(t.criteria)} criteria, {len(t.evidence)} evidence item(s)")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__.strip().splitlines()[-3].strip(), file=sys.stderr)
        print("usage: python3 ingest.py <spec.md>", file=sys.stderr)
        return 2

    try:
        with open(sys.argv[1], "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        print(f"ingest: {exc}", file=sys.stderr)
        return 2

    tasks, refusals = parse(text)

    if refusals:
        print("INGESTION REFUSED:")
        for msg in refusals:
            print(f"  - {msg}")
        print(
            "\nNothing will run. The approved document and the machine's reading of it "
            "do not agree,\nand an output gate cannot catch that."
        )
        return 1

    print_manifest(tasks)
    print(
        "\nConfirm this matches the plan you approved, task by task, before execution starts."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
