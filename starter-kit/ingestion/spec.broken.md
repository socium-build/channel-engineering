# Spec: bounded retry for the upload client

> Derived from the Phase 1 design doc. A human approves this spec before any code
> is generated against it.

**Status:** approved
**Source design doc:** ../corpus/decisions/2026-06-24-bounded-retry-policy.md
**Approved by / date:** j.paul / 2026-06-24

---

## Context: why this work exists

Uploads retry unboundedly against a flaky object store, including on client errors
that will never succeed. A single bad request can generate thousands of calls.

## Goals / Non-goals

- **Goals:** bound retries, back off exponentially, stop retrying 4xx except 429.
- **Non-goals:** changing the upload protocol, adding a queue.

## Requirements

- R1: retries are bounded at a configured maximum.
- R2: 4xx responses are not retried, except 429.

---

## Tasks

### Task 3.1: Add a bounded retry policy module

**Acceptance criteria**

- [ ] Retries stop at `max_retries`, configurable, default 3, hard ceiling 10.
- [ ] Backoff is exponential in the attempt number.

**Evidence to submit**

- `retry_policy_checks` (produced): the gate runs the held-out checks itself.
- `max_retries` (integer): must be <= 10.

**Gate:** independent checker; see [`../gates/`](../gates/).

---

### Task 3.1: Never retry 4xx except 429

**Acceptance criteria**

**Evidence to submit**

- `retry_policy_checks` (produced): output must contain `test_no_retry_on_4xx PASSED`.

**Rollout plan:** ship behind a flag on Tuesday.

---

## Validation notes

- No task advances on a failed gate.
- On pass, the validated decision is appended to the corpus.
