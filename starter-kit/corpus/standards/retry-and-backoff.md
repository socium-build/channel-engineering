# Standard: Retry & Backoff

> Retrieved as project truth when **re-grounding** any task that performs network I/O.

- Retries **MUST** be bounded (default max **10**).
- Backoff **MUST** be exponential, with jitter.
- **Never** retry `4xx` responses except `429 Too Many Requests` (honor `Retry-After`).
- Retries **MUST NOT** mask failures of non-idempotent operations.

*Origin: decision [`bounded-retry-policy`](../decisions/2026-06-24-bounded-retry-policy.md)
(2026-06-24). When this standard changes, add a new decision record; do not silently edit the
rule's history.*
