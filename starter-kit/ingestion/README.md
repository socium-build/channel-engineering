# Starter kit: verify the ingested plan

A human approves a spec. The system then parses that spec into what it will actually run.
**Those two things can differ, and no output gate can catch it**, because the divergence
happened on the way *in*. The model is not diverging from the plan; it is faithfully
executing a plan nobody approved.

That makes ingestion the last checkpoint before execution, not approval.

```
ingest.py         ← parses a spec, prints the manifest it derived, refuses on anything unclear
spec.example.md   ← an approved spec that parses cleanly
spec.broken.md    ← the same spec with three realistic defects
```

## Run it

```bash
python3 ingest.py spec.example.md
```

```
INGESTED PLAN
  phases: 1   tasks: 2

  Phase 3  (2 tasks)
    3.1  Add a bounded retry policy module
          2 criteria, 2 evidence item(s)
    3.2  Never retry 4xx except 429
          2 criteria, 1 evidence item(s)

Confirm this matches the plan you approved, task by task, before execution starts.
```

You approved two tasks. It says two tasks, by name, with their criteria counts. That is the
whole control: the machine states its reading back in a form you can recognize.

Now the same spec with a duplicated task id, a task whose criteria were lost, and a section
the parser does not know:

```bash
python3 ingest.py spec.broken.md
```

```
INGESTION REFUSED:
  - line 55: task 3.1 has an unrecognized section 'Rollout plan'; refusing rather than ignoring it
  - duplicate task 3.1 (lines 31 and 47); ambiguous which one to run
  - task 3.1 has no checkable acceptance criteria; it is a prompt, not a task
```

Every one of those would otherwise be silent. A duplicated id runs one task and drops the
other. Missing criteria produce a task that cannot fail. An unknown section is content the
human wrote and the machine ignored. None of them look like errors at runtime; they look
like a shorter plan that finished sooner.

## The rule that matters

**Refuse, do not guess.** A parser that skips what it does not understand is choosing a plan
on the human's behalf and not telling them. Silent partial acceptance is the failure mode; a
loud refusal is the fix, and it costs one run to correct rather than forty files.

## Minimum viable today

You do not need this script. You need the property. After a human approves a spec and before
execution begins, have the system print what it parsed (phases and tasks, by name and count)
and stop on anything it cannot read cleanly. A diff between that manifest and the approved
document is the check.

If your runner cannot report its own parse, that is worth knowing before you trust it with
forty tasks.
