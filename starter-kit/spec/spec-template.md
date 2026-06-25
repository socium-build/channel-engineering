# Spec: <feature name>

> A spec is the instrument that narrows the output distribution **before** generation.
> Its job is to make every task's success *checkable* — by a gate, not by a vibe.
> A human approves this spec before any code is generated.

**Status:** draft | approved
**Source design doc:** <link to the Phase 1 design doc this spec derives from>
**Approved by / date:** <human> / <date>

---

## Context — why this work exists

<2–4 sentences. The problem, and why now. Pulled from the design doc; don't re-litigate
the design here.>

## Goals / Non-goals

- **Goals:** <what this delivers>
- **Non-goals:** <what this deliberately does not do — bounds the work>

## Requirements

- R1: <requirement>
- R2: <requirement>

---

## Tasks

Each task is small enough to generate, validate, and commit on its own. Every task carries
**checkable acceptance criteria** and names the **evidence** a gate will validate.

### Task 1.1 — <short imperative description>

**Acceptance criteria** (each must be objectively checkable):

- [ ] <criterion — phrased so a script or a reviewer can say yes/no>
- [ ] <criterion>

**Evidence to submit** (artifacts a gate will check, not claims):

- `test_output` (artifact): test run showing `<named test that proves the criterion>`
- `<field>` (<type>): <what it must satisfy, e.g. `max_retries <= 10`>

**Gate:** the acceptance schema for this task is **withheld** from the generating agent.
See [`../gates/`](../gates/) for a runnable gate.

---

### Task 1.2 — <short imperative description>

**Acceptance criteria:**

- [ ] <criterion>

**Evidence to submit:**

- `<field>` (<type>): <constraint>

**Gate:** withheld schema; validated after submission.

---

## Validation notes

- No task advances on a failed gate.
- An autonomous run cannot self-certify past a gate (no model-set "approved" booleans).
- On pass, each validated decision is appended to the corpus so later work can retrieve it.
