# Starter kit: an independent-decision gate

Two runnable, zero-dependency gates for the **most important control in the guide**. They
differ on one question, and the difference is the whole lesson:

| | who supplies the decisive evidence | forgeable |
| --- | --- | --- |
| `gate.py` | the agent submits it | **yes** |
| `gate_produce.py` | the gate runs the check itself | no |

Start with `gate.py` to see the evidence contract and the independent decision point. Then
run the forgery demo below, which breaks it, and see `gate_produce.py` hold.

## The idea

```
gate-spec.example.json     ← the checker's copy of the acceptance criteria. The criteria
                             themselves are public: they live in the approved spec the agent
                             works from. What the agent never gets is the checker to run.
evidence.example.json      ← what the agent submits: claims + pointers to proof artifacts.
artifacts/test.log         ← a proof artifact.
gate.py                    ← validates the submission against the criteria, independently.

produce-spec.example.json  ← the same criteria, expressed as checks the GATE RUNS.
checks/                    ← the held-out check and the code under test.
forged/                    ← a fabricated submission that satisfies gate.py.
gate_produce.py            ← runs the check itself; nothing is submitted to forge.
```

> **`gate_produce.py` fails on purpose until you fix a bug.** `checks/retry_policy.py`
> ships with a deliberate defect so the forgery demo below works out of the box, which
> means *every* run of the producing gate reports `GATE FAILED` until you correct it.
> That is the demo working, not the gate being broken. The fix is one line, and it is
> named at the end of the forgery demo.

The agent knows the contract it must meet (bounded retries at 10, no retry on 4xx, a passing
`no_retry_on_4xx` test), because it cannot build the right thing otherwise. What it does
**not** get is the power to run the checker, edit it, or pass it by asserting success.

Public contract, private verifier. The requirement is disclosed; the verdict is not the
agent's to give.

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

## The forgery demo

`gate.py` rejects self-attestation but trusts the artifact. `forged/` is what an agent does
about that: it never fixed the bug in `checks/retry_policy.py`, and it wrote a test log
saying it did. Every value satisfies the criteria.

```bash
python3 gate.py --spec gate-spec.example.json --evidence forged/evidence.json
# GATE PASSED: all required evidence present and validated.
```

That is the failure the guide warns about, in one command. Now hand the identical forged
submission to the gate that produces its own evidence:

```bash
python3 gate_produce.py --spec produce-spec.example.json --evidence forged/evidence.json
# GATE FAILED:
#   - produced rule 'retry_policy_checks': exit 1, expected 0
#   - produced rule 'retry_policy_checks': output missing 'test_no_retry_on_4xx PASSED'
#   - produced rule 'retry_policy_checks': output contains forbidden 'FAILED'
```

Nothing about the submission changed. What changed is who ran the check. Add `--show-output`
to watch the gate generate the evidence it is judging.

To see the honest path, fix the bug the check catches: in `checks/retry_policy.py`, the 4xx
branch returns `status == 404` where it should return `False`. Correct it and
`gate_produce.py` passes. The repository deliberately ships with that bug in place so the
demo works out of the box.

## What each one proves

`gate.py` demonstrates the **evidence contract** (submit artifacts, not assurances; a bare
`"done": true` cannot satisfy an `artifact` requirement) and the **independent decision
point** (a separate checker renders the verdict, on content, after the fact, and the agent
cannot self-attest past it). It is genuinely useful and it is not tamper-proof: an agent that
can write the artifact can write a convincing one.

`gate_produce.py` closes that seam by moving one thing: the decisive artifact is named in the
*spec* as a command to run, not in the *evidence* as a path to read. The agent supplies
nothing that decides the verdict, so there is nothing for it to forge. Values the gate cannot
produce for itself still come from the agent, under `claimed` rules, and they stay as
trustworthy as any claim.

The remaining boundary is the runner. `gate_produce.py` executes a subprocess on the same
machine; a full implementation runs it somewhere the agent cannot write to at all (CI, a
sandbox, a separate host) and holds back adversarial fixtures the agent never sees.

## Why this is the control to copy first

- **It rejects self-attestation.** `"done": true` can't satisfy an `artifact` requirement.
  The agent cannot certify its own work.
- **Its decision is independent.** The agent submits evidence; it does not run the checker or
  supply the verdict. Even knowing every criterion, it cannot pass by restating it.
- **It can be made unforgeable without new infrastructure.** `gate_produce.py` is the same
  idea with the evidence generated rather than trusted, in about a hundred lines.
- **It needs no daemon.** Wire either script into a pre-commit hook or CI step the agent can't
  run or edit, and you have the independent decision point today.

## Wiring it in

1. Put the acceptance criteria in the spec the agent works from: it must know the contract to
   satisfy it. Keep the *checker* and its execution out of the agent's reach (it can't run
   the gate, edit it, or replace its verdict).
2. Prefer produced evidence. Anything the gate can run for itself, it should run for itself.
   Reserve submitted evidence for values no check can generate.
3. Run the gate in a pre-commit hook or CI; a non-zero exit blocks the commit/merge.
4. On pass, a human promotes the decision + evidence into your corpus (the next control).
