# Decision: bounded-retry-policy

- **Date:** 2026-06-24
- **Status:** validated (gate passed) and human-promoted
- **Task:** 3.2: add bounded retry to the upload client

## Decision

Upload-client retries are bounded at **10**, use **exponential backoff with jitter**, and the
client **does not retry `4xx`** responses (except `429`, honoring `Retry-After`).

## Why

Unbounded retries amplified an upstream outage into a self-inflicted load spike. `4xx`
responses are client errors; retrying them wastes budget and can worsen rate-limiting.

## Evidence

- `test_no_retry_on_4xx` PASSED; full run: 14 passed.
  See [`../../gates/artifacts/test.log`](../../gates/artifacts/test.log).
- Gate: [`../../gates/gate-spec.example.json`](../../gates/gate-spec.example.json). The
  criteria above were public in the approved spec; the gate validated the submitted evidence
  independently, the agent could not run it or self-certify past it.

## Provenance

Extracted verbatim from the Task 3.2 execution, decision + rationale as stated, not a
generated summary. Promoted to a standard: [`../standards/retry-and-backoff.md`](../standards/retry-and-backoff.md).
