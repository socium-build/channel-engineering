# Starter kit: a non-gameable gate

A runnable, zero-dependency reference for the **most important control in the guide**: a
validation gate the generating agent *cannot game*, because it never sees the rubric.

## The idea

```
gate-spec.example.json     ← the acceptance schema. WITHHELD from the generating agent.
evidence.example.json      ← what the agent submits: claims + pointers to proof artifacts.
artifacts/test.log         ← a proof artifact the agent produced.
gate.py                    ← validates the submission against the withheld schema.
```

The agent is told only: *"do the task, then submit an evidence file and the artifacts it
references."* It is **never** shown `gate-spec.example.json`. So it cannot write to the
rubric — it can only do the work and submit proof, which the gate checks after the fact,
down to the *content* of the artifacts.

## Run it

Passing case (the example artifact contains the required proof):

```bash
python3 gate.py --spec gate-spec.example.json --evidence evidence.example.json
# GATE PASSED: all required evidence present and validated.
```

Now make it fail like a real submission would — e.g. claim success without the proof:

```bash
# Point at an artifact that doesn't contain `test_no_retry_on_4xx`, or bump max_retries:
echo '{"test_output": "artifacts/test.log", "max_retries": 99}' > /tmp/bad.json
python3 gate.py --spec gate-spec.example.json --evidence /tmp/bad.json --root .
# GATE FAILED:
#   - field 'max_retries' = 99 exceeds max 10
```

## Why this is the control to copy first

- **It defeats Goodhart.** A model that can't read the criteria can't optimize to them.
- **It rejects self-attestation.** `"done": true` can't satisfy an `artifact` requirement —
  proof must exist on disk and contain what it claims.
- **It needs no daemon.** Wire `gate.py` into a pre-commit hook or CI step, keep the
  gate-spec in a path your agent's prompt/context never includes, and you have a
  non-gameable gate today.

## Wiring it in

1. Keep gate-specs in a directory your agent context **excludes** (don't paste them into
   prompts, don't index them into the agent's retrieval).
2. Have the agent emit `evidence.json` + artifacts at the end of a task.
3. Run `gate.py` in a pre-commit hook or CI; a non-zero exit blocks the commit/merge.
4. On pass, append the decision + evidence to your corpus (the next control).
