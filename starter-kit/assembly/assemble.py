#!/usr/bin/env python3
"""Mode-aware context assembly: a sketch.

Same materials, two assembly orders, because attention is not uniform across the
context window. The goal must sit where attention is highest *for the mode of the work*:

    conversational -> the live tail carries intent (recency-forward)
    autonomous     -> pin the goal at the END, after the pile of intermediate results
                      that would otherwise bury it in the low-attention middle

Zero dependencies; Python 3.8+ standard library only. Read it; it's the point.
"""
from __future__ import annotations

GOAL = "Add bounded retry (max 10, exponential backoff, no retry on 4xx) to the upload client."
SYSTEM = "<system / role prompt>"
CORPUS = [
    "[standard] Retries MUST be bounded; backoff exponential w/ jitter; never retry 4xx except 429.",
]
# In a long autonomous run, history grows large with tool output and buries the goal:
HISTORY = [
    "[assistant] reading upload_client.py ...",
    "[tool] ran tests: 3 passed",
    "[assistant] editing retry handler ...",
    "[tool] ran tests: 14 passed, incl. test_no_retry_on_4xx",
    "[assistant] updating changelog ...",
]


def assemble(mode: str, system: str, corpus: list[str], history: list[str], goal: str) -> list[str]:
    if mode == "conversational":
        # A human is present; the recent tail is the authoritative intent.
        return [system, *corpus, *history]
    if mode == "autonomous":
        # No human; re-pin the goal where attention is highest, at the very end.
        return [system, *corpus, *history, f"CURRENT GOAL (do not lose): {goal}"]
    raise ValueError(f"unknown mode: {mode!r}")


if __name__ == "__main__":
    for mode in ("conversational", "autonomous"):
        print(f"=== {mode} ===")
        blocks = assemble(mode, SYSTEM, CORPUS, HISTORY, GOAL)
        for i, block in enumerate(blocks):
            print(f"  [{i}] {block}")
        tail = blocks[-1]
        note = "goal pinned at the tail" if "CURRENT GOAL" in tail else "tail carries live intent"
        print(f"  -> {note}\n")
