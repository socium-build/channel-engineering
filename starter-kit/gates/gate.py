#!/usr/bin/env python3
"""A minimal, non-gameable validation gate.

The point of this script is the *information asymmetry*, not the validation logic:

    The acceptance schema (gate-spec) is a file the GENERATING AGENT NEVER SEES.
    The agent only knows it must submit an evidence file plus the artifacts it
    references. The gate validates that submission AFTER THE FACT, down to the
    content of the artifacts.

Because the agent cannot read the rubric, it cannot shape its work to pass the
rubric without doing the work. A bare claim ("done": true) cannot satisfy an
`artifact` requirement, and a self-attested boolean is never trusted as proof.

Zero dependencies — Python 3.8+ standard library only.

Usage:
    python3 gate.py --spec gate-spec.example.json --evidence evidence.example.json

Exit code 0 = pass, 1 = gate failed (reasons printed), 2 = bad invocation.
"""
from __future__ import annotations

import argparse
import json
import os
import sys


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def check_field(rule: dict, evidence: dict, root: str) -> list[str]:
    """Return a list of failure messages for one required field (empty = pass)."""
    field = rule["field"]
    ftype = rule.get("type", "string")
    fails: list[str] = []

    if field not in evidence:
        return [f"missing required field '{field}'"]
    value = evidence[field]

    if ftype == "artifact":
        # Must be a path to a file that actually exists; optionally its content
        # must contain a required substring. This is what makes the gate
        # probe-proof: a file's existence and content cannot be faked by a claim.
        if not isinstance(value, str):
            return [f"field '{field}' must be a path string, got {type(value).__name__}"]
        artifact_path = os.path.join(root, value)
        if not os.path.isfile(artifact_path):
            return [f"artifact for '{field}' not found at '{value}'"]
        must_contain = rule.get("must_contain")
        if must_contain:
            with open(artifact_path, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read()
            if must_contain not in content:
                fails.append(
                    f"artifact '{value}' does not contain required proof "
                    f"'{must_contain}'"
                )

    elif ftype == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            return [f"field '{field}' must be an integer, got {type(value).__name__}"]
        if "max" in rule and value > rule["max"]:
            fails.append(f"field '{field}' = {value} exceeds max {rule['max']}")
        if "min" in rule and value < rule["min"]:
            fails.append(f"field '{field}' = {value} below min {rule['min']}")

    elif ftype == "string":
        if not isinstance(value, str):
            return [f"field '{field}' must be a string, got {type(value).__name__}"]
        if rule.get("non_empty") and not value.strip():
            fails.append(f"field '{field}' must be non-empty")

    else:
        fails.append(f"unknown rule type '{ftype}' for field '{field}'")

    return fails


def main() -> int:
    ap = argparse.ArgumentParser(description="Non-gameable validation gate.")
    ap.add_argument("--spec", required=True, help="gate-spec JSON (withheld from the agent)")
    ap.add_argument("--evidence", required=True, help="evidence JSON submitted by the agent")
    ap.add_argument("--root", help="base dir for artifact paths (default: evidence file dir)")
    args = ap.parse_args()

    try:
        spec = load_json(args.spec)
        evidence = load_json(args.evidence)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"gate: could not load inputs: {exc}", file=sys.stderr)
        return 2

    root = args.root or os.path.dirname(os.path.abspath(args.evidence))

    all_fails: list[str] = []
    for rule in spec.get("required", []):
        all_fails.extend(check_field(rule, evidence, root))

    if all_fails:
        print("GATE FAILED:")
        for msg in all_fails:
            print(f"  - {msg}")
        print("\nThe submission did not satisfy the (withheld) acceptance schema.")
        return 1

    print("GATE PASSED: all required evidence present and validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
