#!/usr/bin/env python3
"""The held-out check the gate runs for itself.

The generating agent never runs this and never writes its output. `gate_produce.py`
executes it and reads what comes back, so the evidence is *produced by the verifier*
rather than submitted by the producer.

Zero dependencies. Prints one line per case and a summary line the gate matches on;
exits 0 if every case passed, 1 otherwise.

Usage:
    python3 run_checks.py
"""
from __future__ import annotations

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from retry_policy import MAX_RETRIES, backoff_delay, should_retry  # noqa: E402

# (name, callable): each returns True when the property holds.
CASES = [
    (
        "test_no_retry_on_4xx",
        lambda: not any(should_retry(s, 0) for s in (400, 401, 403, 404, 409, 422)),
    ),
    ("test_retries_on_429", lambda: should_retry(429, 0)),
    ("test_retries_on_5xx", lambda: should_retry(500, 0) and should_retry(503, 0)),
    (
        "test_bounded_at_max_retries",
        lambda: not should_retry(500, MAX_RETRIES),
    ),
    (
        "test_backoff_is_exponential",
        lambda: backoff_delay(0) < backoff_delay(1) < backoff_delay(2)
        and abs(backoff_delay(2) - 4 * backoff_delay(0)) < 1e-9,
    ),
]


def main() -> int:
    failed = 0
    for name, case in CASES:
        try:
            ok = bool(case())
        except Exception as exc:  # a crashing check is a failing check
            ok = False
            print(f"{name} ERROR {exc}")
            failed += 1
            continue
        print(f"{name} {'PASSED' if ok else 'FAILED'}")
        if not ok:
            failed += 1

    passed = len(CASES) - failed
    if failed:
        print(f"\n{failed} failed, {passed} passed")
        return 1
    print(f"\n{passed} passed in 0.00s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
