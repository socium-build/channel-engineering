# Channel Engineering — A Field Guide

A practitioner's guide to making LLM-driven development *reliable*: not by waiting for a
better model, but by engineering the channel the model works through.

This is the **how**. The **why** — the argument that reliability is lost in the channel,
not the model — lives in the companion paper, *Engineering the Channel*
([PDF](docs/engineering-the-channel.pdf)). You don't need to read it first. Read it when you
want the evidence behind a claim here.

> **Status: first complete draft.** All controls are worked in full; the starter kit covers
> specs, gates, corpus, and assembly and runs out of the box. Feedback welcome.

---

## The 60-second contract

If you spend twenty minutes here, you'll leave with: a way to **locate yourself** (the
maturity ladder), a **process** to follow (three phases), and a set of **controls** you can
apply this week with tools you already have. Each control has a falsifiable done-test and a
minimum version you can build without buying anything.

**You have a channel problem if** any of these are true:

- Your AI's "memory" is the chat history, and last week's decisions are effectively gone.
- Your validation is a test suite the model can see — so it writes code to pass the test,
  not to do the work.
- An autonomous run drifts: twenty steps in, the model is solving a problem subtly
  different from the one you gave it.
- When a generation is wrong, your first instinct is to swap models, not to ask what
  context was missing.

None of those are model-capability problems. They're channel problems. This guide is about
fixing the channel.

---

## The shape of the work

Reliable AI development is not one prompt. It is a **three-phase process**, and inside the
last phase, a tight loop:

```
Phase 1                 Phase 2                Phase 3
Conversational   ──▶    Doc ──▶ Structured ──▶ Execute the spec, task by task:
Design → Doc            Spec                   ┌─────────────────────────────────┐
                                               │ re-ground → generate → GATE →   │
(human + AI think       (every task gets       │ update corpus → next task       │
 together; the durable   checkable acceptance  └─────────────────────────────────┘
 output is a design doc) criteria; a human      a failed gate halts advancement;
                         approves before code)  the run cannot self-certify
```

Two stances hold across all three phases:

- **Own the loop you intend to engineer.** The controls that make a channel reliable —
  assembly order, retention, gate placement — only exist for whoever owns the agent loop. A
  config layered on top of an agent you don't control can *influence* the channel but can't
  *engineer* it.
- **Reliability is a channel problem, not a model problem.** When output doesn't match
  intent, diagnose the channel: what context was missing, what spec was ambiguous, what gate
  let it through. The model is a component; the channel is the system.

---

## The maturity ladder — where are you?

| Level | You are here if… | The gap to the next rung |
|---|---|---|
| **L0 — Vibe prompting** | Single prompts, no spec, no gate; memory is the chat log. | Start curating what enters the window. |
| **L1 — Curated context** | You pack the window well — but from inside a loop you don't own. | Put a *spec* in front of generation. |
| **L2 — Specs + advisory checks** | You write specs; tests exist but are visible/advisory (gameable). | Make the gate **non-gameable**; make memory **deterministic**. |
| **L3 — Gated + durable** | Withheld-schema gates; validated work persists extractively. | Own the loop end to end; re-ground every step. |
| **L4 — Owned & re-grounded** | You control assembly/retention; re-ground at each step; reliability compounds. | — (this is the target) |

You don't need L4 to benefit. Most teams are at L0–L1 and the jump to L2 is the highest-ROI
move available. Each control below tells you which rung it buys.

---

## The process

### Foundations

These stances hold in every phase.

#### Own the loop you intend to engineer  ·  *foundational*

**Do this.** Build or adopt a substrate where *you* control assembly order, token budget,
retention, and gate placement. If those knobs belong to someone else's closed product, you
can influence the channel but not engineer it.

**You've done it when.** You can change what enters the window, in what order, and what
persists after a turn — without filing a vendor feature request.

**Anti-pattern.** Tuning a wrapper on a closed agent and calling it reliability engineering.

**Minimum viable today.** A thin orchestration script you own — assemble prompt → call model
→ run gate → write corpus — beats a richer agent you don't control. Own the smallest loop
end to end.

*Prevents: a hard ceiling on reliability — you can't fix what you can't reach.*

#### Treat the context window as a communication channel  ·  *foundational*

**Do this.** Treat every token as occupying a finite, lossy channel. Each one should narrow
the output toward what you want; if it isn't, it's noise degrading the signal.

**You've done it when.** You can point at any token in the window and name what it narrows.
If you can't, it's noise you're spending attention budget to carry.

**Anti-pattern.** Stuffing the window "just in case" — whole files, full histories, every
doc. More context is not more signal; position effects and rot let the goal drown.

**Minimum viable today.** Audit one real prompt: delete anything you can't justify as
narrowing the output. Watch what happens.

*Prevents: context rot, lost-in-the-middle, the goal aging out under noise.*

#### Treat reliability as a channel problem, not a model problem  ·  *foundational*

**Do this.** When output doesn't match intent, debug the channel before the model: what
context was missing, what spec was ambiguous, what gate failed to catch it.

**You've done it when.** Your first move on a failure is a channel question, not a model swap.

**Anti-pattern.** "The model isn't smart enough" → upgrade → same failures, because the cause
was a missing spec, not a missing IQ.

**Minimum viable today.** Keep a one-line failure log: for each bad generation, record the
channel cause (missing context / ambiguous spec / weak gate). Patterns surface fast.

*Prevents: chasing model upgrades to fix process defects.*

### Phase 1 — Conversational Design → Doc

The human and the AI think together in open conversation; the **durable output is a design
document**, not the transcript. The conversation is where ambiguity is resolved; the doc is
what survives it.

#### Assemble for the mode  ·  *buys L3*

**Do this.** Use a different assembly strategy for human-in-the-loop vs autonomous work. With
a human present, let the recent conversational tail carry intent (recency-forward). When the
model runs unattended, **pin the goal** and re-present it where attention is highest, so it
can't age out beneath intermediate results.

**You've done it when.** At step 20 of an unattended run, the goal still sits where attention
is highest; in conversation, the model follows the live thread without being over-anchored to
the original ask.

**Anti-pattern.** One uniform context strategy for both modes — recency-forward autonomy lets
tool output bury the goal; pinned-goal conversation ignores the human's live redirection.

**Minimum viable today.** In any autonomous loop, re-inject the goal/spec at the *end* of the
prompt each step. One line of code; outsized effect. See [`starter-kit/assembly/`](starter-kit/assembly/).

*Prevents: goal drift in long autonomous runs; over-anchoring in conversation.*

#### Ground the conversation in project truth  ·  *buys L1 → L2*

**Do this.** Before the design conversation settles anything, retrieve the project's existing
standards and decisions and put them in front of the model. Decide against project truth, not
the model's training-data priors.

**You've done it when.** The resulting design doc aligns with (or explicitly revisits)
existing decisions rather than silently reinventing or contradicting them.

**Anti-pattern.** Designing in a vacuum, then discovering the decision contradicts a standard
the team set six months ago.

**Minimum viable today.** Keep a `/standards` (or `/corpus`) dir; paste the relevant files
into the design conversation. Automate retrieval later.

*Prevents: re-litigating settled decisions; design that drifts from project reality.*

#### Extract the doc; a human approves it  ·  *buys L2*

**Do this.** The durable output of Phase 1 is a **design document** — extracted from the
conversation, not the transcript — and a human approves it before it becomes a spec. Capture
by extraction (real decisions with their rationale), never by asking the model to "summarize
the chat."

**You've done it when.** There's an approved design doc a newcomer could read to understand
the decision and why — and it contains nothing no one actually decided.

**Anti-pattern.** Letting the chat log *be* the design record; or accepting a generated
summary that quietly invents a rationale nobody gave.

**Minimum viable today.** End each design session by writing a short decision doc (the model
may draft, you edit and approve); commit it to the corpus.

*Prevents: lost decisions; hallucinated rationale entering the record.*

### Phase 2 — Doc → Structured Spec

The approved design doc becomes a **structured spec**: a task breakdown where every task
carries explicit, **checkable** acceptance criteria. This is the moment the output
distribution is narrowed — before a line of code is generated.

#### Write the spec before generating  ·  *buys L1 → L2*

**Do this.** Turn the approved design doc into a task breakdown where every task has explicit,
**checkable** acceptance criteria and names the **evidence** a gate will validate. The spec
narrows the output distribution before generation begins.

**You've done it when.** For every task, you can state how its output will be checked —
*before* a line is generated. If you can't, it's a prompt, not a spec.

**Anti-pattern.** "Build me X," with success defined after the fact by eyeballing the result.

**Minimum viable today.** Use [`starter-kit/spec/spec-template.md`](starter-kit/spec/spec-template.md);
require every task to carry at least one checkable criterion and one named artifact.

*Prevents: ambiguous targets; un-checkable "done"; scope drift.*

#### Gate the spec: a human approves before execution  ·  *buys L2 → L3*

**Do this.** The spec is itself gated — a human reviews and approves the human-readable
artifact before any code is generated against it. The most leveraged review you do is on
*intent*, not output.

**You've done it when.** No execution run starts against an unapproved spec, and approval is
recorded.

**Anti-pattern.** Jumping from a rough idea straight to autonomous execution — then finding
the spec was wrong after 40 files changed.

**Minimum viable today.** A required approval step (even a checkbox + a commit) between spec
and execution.

*Prevents: confidently executing the wrong thing; expensive late rework.*

### Phase 3 — Execute the Spec

Implementation proceeds one task at a time, through a tight loop: **re-ground → generate →
gate → update corpus → next task.** We lead with the keystone — the non-gameable gate — then
the rest of the loop.

#### Make the gate non-gameable  ·  *buys L2 → L3*  ·  keystone

**Do this.** Validate *submitted evidence* after the fact. Keep the acceptance schema **out
of the generating agent's context** — the agent should only know "submit proof," never the
rubric it will be judged against.

**You've done it when.** An agent that could read the gate's criteria still couldn't pass
without doing the work. If reading the rubric is enough to pass, it's a rubric, not a gate.

**Looks like.** A single task, traced:

```
Spec      Task 3.2 "add bounded retry to the upload client" — one checkable criterion:
          retries are bounded, backoff is exponential, a test proves no retry on a 4xx.

Gate      The schema the gate checks — never shown to the generating agent:
(withheld)    require test_output : artifact
              assert  max_retries <= 10
              assert  proof : no_retry_on_4xx
          The agent cannot shape its work to a rubric it cannot read.

Proof     It submits artifacts, not assurances:
              test_output: 14 passed, incl. test_no_retry_on_4xx
          The gate checks the artifact's *content*; a bare "done" does not pass.

Corpus    On a pass, the decision and its evidence join the durable corpus —
          retrievable months later by a fresh session that never saw this task.
```

A runnable reference gate is in [`starter-kit/gates/`](starter-kit/gates/): the schema lives
in a file the agent's context never loads; the gate validates a submitted evidence file plus
its artifacts and exits non-zero on any failure.

**Anti-pattern.** `human_approved: true` as a model-set boolean. Self-attestation is the #1
gaming vector — the model certifies its own work.

**Minimum viable today.** You don't need a daemon. A pre-commit hook that runs a gate script
against a spec file the model's prompt never includes gets you most of the way with tools you
already have.

*Prevents: Goodhart / spec-gaming, silent self-certification.*

The other controls in the loop:

#### Re-ground at every step  ·  *buys L3 → L4*

**Do this.** Before each task's generation, retrieve the relevant project truth *again*
rather than trusting residue left in the window. Re-anchor every step; the channel is
engineered continuously, not configured once.

**You've done it when.** The number of steps between two retrievals of project truth is small
— ideally one. Every step in that gap is one where the model trusts window residue and error
compounds.

**Anti-pattern.** Front-loading all context at step 0 and letting it decay across a long run.

**Minimum viable today.** In your execution loop, retrieve the standards relevant to the
*current* task at the start of each task — not once at the top.

*Prevents: compounding drift; decisions made on stale or forgotten context.*

#### Keep durable memory deterministic  ·  *buys L2 → L3*

**Do this.** When memory must be condensed to fit, prefer **extraction** (selecting verbatim
content with its provenance) over generative summary. A summary that hallucinates poisons
every future retrieval; extraction can only omit, never invent.

**You've done it when.** Condensing the corpus can never produce a sentence no source ever
wrote. If it can, it's summarizing, not retaining.

**Anti-pattern.** Asking the model to "compact the history" into a generated summary that
becomes load-bearing memory — a measured reliability regression, not a convenience.

**Minimum viable today.** When you trim memory, cut by selecting and keeping real excerpts
(with source links), not by generating a paraphrase.

*Prevents: hallucinated memory poisoning every downstream retrieval.*

#### Update the corpus on every validated decision  ·  *buys L3*

**Do this.** Every decision that passes a gate is appended to the durable, retrievable corpus
— with its evidence. The corpus grows through the work; uncaptured decisions are lost, and
their absence degrades future generations.

**You've done it when.** You can ask "where does last week's validated decision live?" and the
answer is the corpus, not the chat history.

**Anti-pattern.** Decisions living only in PR threads, Slack, and chat logs — unreachable at
generation time.

**Minimum viable today.** A git-tracked `/corpus` dir; on each gate pass, append a short
decision record (what, why, evidence link). See [`starter-kit/corpus/`](starter-kit/corpus/).

*Prevents: repeated mistakes; loss of hard-won decisions; ungrounded future work.*

---

## Starter kit

Real, clonable artifacts — not pseudocode. Together they trace one coherent example (a
bounded-retry policy) across the whole loop:

- [`starter-kit/spec/spec-template.md`](starter-kit/spec/spec-template.md) — a **spec
  skeleton** with checkable, per-task acceptance criteria.
- [`starter-kit/gates/`](starter-kit/gates/) — a zero-dependency, runnable **non-gameable
  gate** (withheld schema + evidence validator), with an example schema and submission.
- [`starter-kit/corpus/`](starter-kit/corpus/) — a **deterministic corpus** layout: a
  git-tracked decision record and the standard it produces, the kind you retrieve when
  re-grounding the next task.
- [`starter-kit/assembly/`](starter-kit/assembly/) — a **mode-aware assembly** sketch:
  recency-forward for conversation, pinned-goal for autonomy.

---

## Where Socium fits

This guide is the method. Doing it by hand is *laborious* — non-gameable gates, deterministic
retention, and re-grounding at every step are real work to assemble and keep honest.
[Socium](https://socium.build) is the substrate that runs this loop for you, end to end, so the
gates are non-gameable and the corpus is deterministic by default instead of by discipline.

This guide stands on its own. Socium is the easy way to live by it.

---

## License

- **Prose / documentation:** [CC-BY-4.0](LICENSE-docs.md) — use and adapt freely, with
  attribution.
- **Code / templates** (`starter-kit/`): [MIT](LICENSE).

Channel engineering is meant to be adopted. Attribution is all we ask.
