# Starter kit: an approval a timeout denies

Most human-in-the-loop code asks for approval and then, when nobody answers, proceeds. That
hands the model its widest latitude at the exact moment the least oversight is present.

This inverts it. **When the human cannot be reached, the run does less, not more.**

```
approval.py   ← classify(action) → routine or consequential; request() denies on timeout
```

## Run it

```bash
python3 approval.py
```

```
A run proceeding while the human is unreachable.

  ALLOW  edit upload_client/retry_policy.py: routine, in mandate, reversible
  ALLOW  run tests/test_retry_policy.py: routine, in mandate, reversible
  DENY   delete upload_client/legacy_uploader.py: consequential ('delete' is hard to reverse); human unreachable
  DENY   edit infra/production.tf: consequential ('infra/production.tf' is outside the run's mandate); human unreachable
  DENY   deploy upload_client: consequential ('deploy' is hard to reverse); human unreachable

2 of 5 actions proceeded. The run did less, not more.
```

The run kept working. It read files, ran tests, edited code inside its mandate. It just did
not delete, deploy, or reach outside what it was authorized to touch, and it did not need
anyone present to stop it.

`--interactive` prompts for real, with a five second timeout. Answer nothing and watch it
deny.

## The two ways an action becomes consequential

**Hard to reverse.** Delete, deploy, publish, send, pay, rotate a credential. The verb list
in `approval.py` is deliberately short and deliberately yours to edit.

**Outside the mandate.** An action can be perfectly reversible and still be something this
run was never authorized to do. Editing `infra/production.tf` is a text edit; it is also not
what the run was approved for. Scope is a separate axis from reversibility, and both deny.

## Why the default matters more than the prompt

Any approval mechanism looks the same when the human is at the keyboard. The design shows
itself when they are not, and there are only two possible defaults:

- **Timeout allows.** Oversight degrades, authority expands. The run's most consequential
  moments happen precisely when nobody is checking.
- **Timeout denies.** Oversight degrades, authority contracts. The run stops and waits.

Silence is not consent. An absent human is not a green light. The failure mode of denying is
a run that halts and needs restarting, which costs minutes. The failure mode of allowing is
an unreviewed irreversible action, which can cost anything.

## Minimum viable today

In whatever autonomous loop you already have:

1. Write down the mandate: what this run may touch.
2. Mark the consequential actions: writes outside the mandate, deletes, external calls,
   anything hard to undo.
3. Make those require an explicit approval, and make the timeout **deny**.

Step 3 is usually a one-line change to code you already have, and it is the whole control.
