#!/usr/bin/env python3
"""A validation gate that PRODUCES its own evidence.

`gate.py` in this directory validates evidence the agent *submits*. That catches
self-attestation ("done": true) but not forgery: an agent that can write the
artifact can write a convincing one. This script closes that seam.

The difference is one line of authority:

    gate.py          reads an artifact path the agent put in the evidence file
    gate_produce.py  runs a command named in the SPEC and reads its own output

The agent never supplies the decisive artifact, so there is nothing for it to
forge. It can still be asked for claimed values (a version, a config number), but
anything the gate can produce, the gate produces.

Zero dependencies; Python 3.8+ standard library only.

Usage:
    python3 gate_produce.py --spec produce-spec.example.json
    python3 gate_produce.py --spec produce-spec.example.json --evidence forged/evidence.json

Exit code 0 = pass, 1 = gate failed (reasons printed), 2 = bad invocation.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def run_produced(rule: dict, root: str) -> "tuple[list[str], str]":
    """Execute one produced-evidence rule. Returns (failures, captured output)."""
    name = rule.get("name", "<unnamed>")
    cmd = rule.get("run")
    fails: list[str] = []

    if not isinstance(cmd, list) or not cmd:
        return ([f"produced rule '{name}': 'run' must be a non-empty argv list"], "")

    try:
        proc = subprocess.run(
            cmd,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=rule.get("timeout_s", 60),
        )
    except FileNotFoundError:
        return ([f"produced rule '{name}': command not found: {cmd[0]}"], "")
    except subprocess.TimeoutExpired:
        return ([f"produced rule '{name}': timed out"], "")

    output = (proc.stdout or "") + (proc.stderr or "")

    expected_exit = rule.get("must_exit", 0)
    if proc.returncode != expected_exit:
        fails.append(
            f"produced rule '{name}': exit {proc.returncode}, expected {expected_exit}"
        )

    for needle in rule.get("must_contain", []):
        if needle not in output:
            fails.append(f"produced rule '{name}': output missing '{needle}'")

    for needle in rule.get("must_not_contain", []):
        if needle in output:
            fails.append(f"produced rule '{name}': output contains forbidden '{needle}'")

    return (fails, output)


def check_claimed(rule: dict, evidence: dict) -> list[str]:
    """Validate a value the agent claims. Only for things the gate cannot produce."""
    field = rule["field"]
    if field not in evidence:
        return [f"missing claimed field '{field}'"]
    value = evidence[field]
    if isinstance(value, bool) or not isinstance(value, int):
        return [f"claimed field '{field}' must be an integer, got {type(value).__name__}"]
    fails = []
    if "max" in rule and value > rule["max"]:
        fails.append(f"claimed field '{field}' = {value} exceeds max {rule['max']}")
    if "min" in rule and value < rule["min"]:
        fails.append(f"claimed field '{field}' = {value} below min {rule['min']}")
    return fails


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validation gate that produces its own evidence by running the check itself."
    )
    ap.add_argument("--spec", required=True, help="gate-spec JSON naming the checks to RUN")
    ap.add_argument(
        "--evidence",
        help="optional evidence JSON, for claimed values the gate cannot produce",
    )
    ap.add_argument("--root", help="working dir for produced commands (default: spec file dir)")
    ap.add_argument("--show-output", action="store_true", help="print what the checks emitted")
    args = ap.parse_args()

    try:
        spec = load_json(args.spec)
        evidence = load_json(args.evidence) if args.evidence else {}
    except (OSError, json.JSONDecodeError) as exc:
        print(f"gate: could not load inputs: {exc}", file=sys.stderr)
        return 2

    root = args.root or os.path.dirname(os.path.abspath(args.spec))

    all_fails: list[str] = []

    for rule in spec.get("produced", []):
        fails, output = run_produced(rule, root)
        all_fails.extend(fails)
        if args.show_output and output:
            print(f"--- output of '{rule.get('name', '<unnamed>')}' ---")
            print(output.rstrip())
            print("--- end output ---\n")

    for rule in spec.get("claimed", []):
        all_fails.extend(check_claimed(rule, evidence))

    if all_fails:
        print("GATE FAILED:")
        for msg in all_fails:
            print(f"  - {msg}")
        print("\nEvidence was produced by the gate, not submitted. No artifact could have changed this.")
        return 1

    print("GATE PASSED: every decisive check was run by the gate itself.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
