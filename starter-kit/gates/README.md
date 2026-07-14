# Starter kit: an independent-decision gate

A runnable, zero-dependency reference for the **most important control in the guide**: a
validation gate whose *verdict* is independent of the generating agent. The agent does the
work and submits evidence; a separate checker renders the decision after the fact, on the
content of the artifacts. The agent cannot render the verdict, and a bare "done" cannot pass.

## The idea

```
gate-spec.example.json     ← the checker's copy of the acceptance criteria. The criteria
                             themselves are public: they live in the approved spec the agent
                             works from. What the agent never gets is the checker to run.
evidence.example.json      ← what the agent submits: claims + pointers to proof artifacts.
artifacts/test.log         ← a proof artifact.
gate.py                    ← validates the submission against the criteria, independently.
```

The agent knows the contract it must meet (bounded retries at 10, no retry on 4xx, a passing
`no_retry_on_4xx` test), because it cannot build the right thing otherwise. What it does
**not** get is the power to run the checker, edit it, or pass it by asserting success.

Public contract, private verifier. The requirement is disclosed; the verdict is not the
agent's to give.

## What this proves, and what it doesn't

This script demonstrates two real things: the **evidence contract** (submit artifacts, not
assurances; a bare `"done": true` cannot satisfy an `artifact` requirement) and the
**independent decision point** (a separate checker renders the verdict, on content, after the
fact, and the agent cannot self-attest past it).

It does **not**, by itself, prove the evidence is genuine. It checks a `test.log` that the
agent submits, and an agent that can write that file can forge its contents. So this is not
tamper-proof. To close that gap, the gate must *produce* the evidence rather than trust it:
run the held-out test itself, or read output from a runner (CI, a sandbox) the agent cannot
write to. That boundary is exactly what a full implementation (Socium) supplies, and what a
do-it-by-hand version has to add deliberately. Treat this script as the contract and the
decision point, not as complete anti-forgery.

## Run it

Passing case (the example artifact contains the required proof):

```bash
python3 gate.py --spec gate-spec.example.json --evidence evidence.example.json
# GATE PASSED: all required evidence present and validated.
```

Now make it fail like a real submission would, e.g. claim success without the proof:

```bash
# Point at an artifact that doesn't contain `test_no_retry_on_4xx`, or bump max_retries:
echo '{"test_output": "artifacts/test.log", "max_retries": 99}' > /tmp/bad.json
python3 gate.py --spec gate-spec.example.json --evidence /tmp/bad.json --root .
# GATE FAILED:
#   - field 'max_retries' = 99 exceeds max 10
```

## Why this is the control to copy first

- **It rejects self-attestation.** `"done": true` can't satisfy an `artifact` requirement.
  The agent cannot certify its own work.
- **Its decision is independent.** The agent submits evidence; it does not run the checker or
  supply the verdict. Even knowing every criterion, it cannot pass by restating it.
- **It marks the seam to harden.** Make the evidence *unforgeable* by having the gate generate
  it (run the test, read a trusted runner's output), not by trusting a log the agent hands you.
- **It needs no daemon.** Wire `gate.py` into a pre-commit hook or CI step the agent can't run
  or edit, and you have the independent decision point today.

## Wiring it in

1. Put the acceptance criteria in the spec the agent works from: it must know the contract to
   satisfy it. Keep the *checker* and its execution out of the agent's reach (it can't run
   `gate.py`, edit it, or replace its verdict).
2. Have the agent emit `evidence.json` + artifacts at the end of a task. For evidence that
   cannot be forged, have the gate *produce* it (run the check itself, or read a trusted
   runner's output) rather than trusting an agent-written log.
3. Run `gate.py` in a pre-commit hook or CI; a non-zero exit blocks the commit/merge.
4. On pass, a human promotes the decision + evidence into your corpus (the next control).
