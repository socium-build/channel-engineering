#!/usr/bin/env python3
"""Absence is not permission: an approval that a timeout DENIES.

Most human-in-the-loop code asks for approval and then, when nobody answers,
proceeds. That gives the model its widest latitude at the exact moment the least
oversight is present. This inverts it: when the human cannot be reached, the run
does less, not more.

Two pieces, both small:

  classify()  decides whether an action is routine or consequential, from the
              action itself. Consequential means hard to reverse, or outside the
              approved mandate.

  request()   asks for approval on consequential actions and returns DENIED on
              timeout. Routine actions never ask.

The mandate is the other half. An action can be perfectly reversible and still be
outside what the run was authorized to do, and that is a denial too.

Zero dependencies; Python 3.8+ standard library only.

Usage:
    python3 approval.py            # runs the scripted demo, no input needed
    python3 approval.py --interactive
"""
from __future__ import annotations

import argparse
import select
import sys

# Verbs whose effects are hard or impossible to walk back.
IRREVERSIBLE = ("delete", "drop", "rm", "purge", "revoke", "rotate", "publish", "deploy", "send", "pay")

# What this run was authorized to touch. Anything else is outside the mandate,
# reversible or not.
MANDATE = ("upload_client", "retry_policy", "tests/")

ALLOW, DENY = "ALLOW", "DENY"


class Decision:
    def __init__(self, verdict: str, reason: str):
        self.verdict = verdict
        self.reason = reason

    @property
    def allowed(self) -> bool:
        return self.verdict == ALLOW

    def __str__(self) -> str:
        return f"{self.verdict:5}  {self.reason}"


def classify(action: str, target: str) -> "tuple[bool, str]":
    """Return (is_consequential, why)."""
    verb = action.strip().lower()
    if any(verb.startswith(v) for v in IRREVERSIBLE):
        return True, f"'{action}' is hard to reverse"
    if not any(scope in target for scope in MANDATE):
        return True, f"'{target}' is outside the run's mandate {MANDATE}"
    return False, "routine, in mandate, reversible"


def ask_human(prompt: str, timeout_s: float) -> "str | None":
    """Return the human's answer, or None if they could not be reached in time."""
    print(f"{prompt} [y/N] (denies in {timeout_s:g}s) ", end="", flush=True)
    ready, _, _ = select.select([sys.stdin], [], [], timeout_s)
    if not ready:
        print("\n  (no answer)")
        return None
    return sys.stdin.readline().strip().lower()


def request(action: str, target: str, *, timeout_s: float = 5.0, reachable: bool = True) -> Decision:
    """Authorize one action. Consequential actions deny unless explicitly approved."""
    consequential, why = classify(action, target)
    if not consequential:
        return Decision(ALLOW, f"{action} {target}: {why}")

    if not reachable:
        return Decision(DENY, f"{action} {target}: consequential ({why}); human unreachable")

    answer = ask_human(f"  approve: {action} {target}?", timeout_s)
    if answer is None:
        return Decision(DENY, f"{action} {target}: consequential ({why}); no answer before timeout")
    if answer in ("y", "yes"):
        return Decision(ALLOW, f"{action} {target}: explicitly approved by a human")
    return Decision(DENY, f"{action} {target}: explicitly denied")


DEMO = [
    ("edit", "upload_client/retry_policy.py", True),
    ("run", "tests/test_retry_policy.py", True),
    ("delete", "upload_client/legacy_uploader.py", False),
    ("edit", "infra/production.tf", False),
    ("deploy", "upload_client", False),
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Approval that a timeout denies.")
    ap.add_argument("--interactive", action="store_true", help="actually prompt (5s timeout)")
    args = ap.parse_args()

    if args.interactive:
        for action, target, _ in DEMO:
            print(request(action, target, timeout_s=5.0, reachable=True))
        return 0

    print("A run proceeding while the human is unreachable.\n")
    allowed = 0
    for action, target, reachable in DEMO:
        d = request(action, target, reachable=reachable)
        allowed += d.allowed
        print(f"  {d}")
    print(
        f"\n{allowed} of {len(DEMO)} actions proceeded. The run did less, not more.\n"
        "Nothing consequential happened on a guess, and nothing needed a human to say no."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
