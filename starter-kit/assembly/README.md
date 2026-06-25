# Starter kit: mode-aware context assembly

Attention is **not uniform** across the context window. Models attend most strongly to the
start and the end; the middle is where information is lost ("lost-in-the-middle"). So *where*
you place the goal matters — and the right placement depends on the **mode of the work**.

- **Conversational (human in the loop).** The live conversational tail is the authoritative
  statement of intent. Assemble **recency-forward** and let the tail carry the goal; pinning a
  stale original ask fights the human's live redirection.
- **Autonomous (no human).** Intermediate results — tool output, file dumps — pile up and
  **bury the original goal** in the low-attention middle. Re-present the goal where attention
  is highest: **pinned at the very end**, after the noise, every step.

One uniform strategy cannot serve both. That is the whole control.

## Run the sketch

```bash
python3 assemble.py
```

It assembles the *same* materials two ways and prints the resulting block order, so you can
see the goal's position differ by mode. `assemble.py` is ~30 lines of zero-dependency Python —
read it; it's the point, not the plumbing.

## Minimum viable today

In any autonomous loop you already have, append one line to the end of the prompt each step:

```
CURRENT GOAL (do not lose): <the goal / current task spec>
```

That single move — re-pinning intent where attention is highest — is the highest-ROI fix for
goal drift in long runs.
