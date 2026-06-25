# Starter kit: a deterministic corpus

The corpus is the project's durable, retrievable memory. Two rules make it trustworthy:

1. **It only grows through validated work.** A decision enters the corpus when it passes a
   gate — with its evidence. (See [`../gates/`](../gates/).)
2. **It is extractive, never generative.** Entries are real decisions and excerpts with
   provenance. Nothing is a model-generated summary that could invent a rationale no one gave.
   Extraction can omit; it can never invent.

## Layout

```
corpus/
  decisions/   one record per validated decision (what, why, evidence)
  standards/   the durable rules those decisions produce — what you retrieve when re-grounding
```

## Why git-tracked

The corpus is committed alongside the code. It is reviewable, diffable, and **deterministic**:
the same retrieval returns the same content every time. Runtime indexes over it (vector/FTS)
can be rebuilt at will; the corpus files themselves are the source of truth.

## The loop

A gate pass appends a record to `decisions/`. Durable rules get promoted into `standards/`.
The next task retrieves those standards when it **re-grounds**. That is how each validated
task leaves the next one better grounded than the last.

This example traces the same bounded-retry policy used in [`../gates/`](../gates/) and
[`../spec/spec-template.md`](../spec/spec-template.md).
