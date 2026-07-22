# Channel Engineering: A Field Guide

A practitioner's guide to making LLM-driven development *reliable*: not by waiting for a
better model, but by engineering the channel the model works through.

This is the **how**. The **why** (the argument that reliability is lost in the channel,
not the model) lives in the companion paper, *Engineering the Channel*
([PDF](docs/engineering-the-channel.pdf)). You don't need to read it first. Read it when you
want the evidence behind a claim here.

> **Status: first complete draft.** All controls are worked in full; the starter kit covers
> specs, gates, ingestion, authority, corpus, and assembly, and runs out of the box.
> Feedback welcome.

---

## The 60-second contract

If you spend twenty minutes here, you'll leave with: a way to **locate yourself** (the
maturity ladder), a **process** to follow (three phases), and a set of **controls** you can
apply this week with tools you already have. Each control has a falsifiable done-test and a
minimum version you can build without buying anything.

**You have a channel problem if** any of these are true:

- Your AI's "memory" is the chat history, and last week's decisions are effectively gone.
- Your validation is something the model can satisfy by assertion, or a check it can run and
  overfit to, so it writes code to pass the check, not to do the work.
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

- **Own the loop you intend to engineer.** The controls that make a channel reliable
  (assembly order, retention, gate placement) only exist for whoever owns the agent loop. A
  config layered on top of an agent you don't control can *influence* the channel but can't
  *engineer* it.
- **Reliability is a channel problem, not a model problem.** When output doesn't match
  intent, diagnose the channel: what context was missing, what spec was ambiguous, what gate
  let it through. The model is a component; the channel is the system.

---

## The maturity ladder: where are you?

| Level | You are here if… | The gap to the next rung |
|---|---|---|
| **L0: Vibe prompting** | Single prompts, no spec, no gate; memory is the chat log. | Start curating what enters the window. |
| **L1: Curated context** | You pack the window well, but from inside a loop you don't own. | Put a *spec* in front of generation. |
| **L2: Specs + advisory checks** | You write specs; tests exist but are advisory or self-attested (gameable). | Make the gate **independent and tamper-resistant**; make memory **deterministic**. |
| **L3: Gated + durable** | Independent gates (the agent can't run them or self-certify past them); validated work persists extractively. | Own the loop end to end; re-ground every step. |
| **L4: Owned & re-grounded** | You control assembly/retention; re-ground at each step; reliability compounds. | None; this is the target. |

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
persists after a turn, without filing a vendor feature request.

**Anti-pattern.** Tuning a wrapper on a closed agent and calling it reliability engineering.

**Minimum viable today.** A thin orchestration script you own (assemble prompt → call model
→ run gate → write corpus) beats a richer agent you don't control. Own the smallest loop
end to end.

*Prevents: a hard ceiling on reliability: you can't fix what you can't reach.*

#### Treat the context window as a communication channel  ·  *foundational*

**Do this.** Treat every token as occupying a finite, lossy channel. Each one should narrow
the output toward what you want; if it isn't, it's noise degrading the signal.

**You've done it when.** You can point at any token in the window and name what it narrows.
If you can't, it's noise you're spending attention budget to carry.

**Anti-pattern.** Stuffing the window "just in case": whole files, full histories, every
doc. More context is not more signal; position effects and rot let the goal drown.

**Minimum viable today.** Audit one real prompt: delete anything you can't justify as
narrowing the output. Watch what happens.

*Prevents: context rot, lost-in-the-middle, the goal aging out under noise.*

#### Treat the window as a viewport, not a buffer  ·  *foundational*

**Do this.** The window is not a container the work must fit inside. It is a *viewport*: a
bounded, moving projection over a durable record that lives outside the window. Keep the
record of the work (specs, decisions, standards, evidence) durable and outside the window,
and project only what the current step needs into the window, re-aimed each step. Never
compress the record to fit the window. Re-project instead.

**You've done it when.** The record of a task can outgrow the window many times over and the
work still proceeds, because no step needs the whole record in view, only a well-chosen
slice of it.

**Anti-pattern.** Treating a full window as both the goal and the problem: growing the window
and summarizing history to cram the work in. The unit of delivery (a feature, hundreds of
steps across days) is always larger than the unit of attention (one window). Trying to make
them equal is the wrong fight.

**Minimum viable today.** Keep your specs, decisions, and standards in durable files, not in
the chat. At each step, load only the slice relevant to that step. Let the record grow; keep
the window small and aimed.

*Prevents: the whole project trying to live in one window; lossy summaries of history
poisoning later work; the goal drowning as the window fills.*

#### Treat reliability as a channel problem, not a model problem  ·  *foundational*

**Do this.** When output doesn't match intent, debug the channel before the model: what
context was missing, what spec was ambiguous, what gate failed to catch it.

**You've done it when.** Your first move on a failure is a channel question, not a model swap.

**Anti-pattern.** "The model isn't smart enough" → upgrade → same failures, because the cause
was a missing spec, not a missing IQ.

**Minimum viable today.** Keep a one-line failure log: for each bad generation, record the
channel cause (missing context / ambiguous spec / weak gate). Patterns surface fast.

*Prevents: chasing model upgrades to fix process defects.*

#### When you can't be reached, the run does less, not more  ·  *foundational*

**Do this.** Decide, before an autonomous run, what it may do without you and what it may not.
When you become unreachable, degraded oversight should narrow the run's authority, not widen
it. Consequential actions (anything hard to reverse, or outside the approved mandate) deny by
default when they cannot get human judgment. Absence is not permission.

**You've done it when.** A run that hits a consequential decision it wasn't authorized for,
while you are unreachable, stops and waits rather than proceeding on its own guess.

**Anti-pattern.** Treating an absent human as a green light, so the model gains the most
latitude exactly when the least oversight is present. Silence is not consent.

**Minimum viable today.** In your autonomous loop, mark which actions are consequential
(writes, deletes, external calls, anything outside the task's mandate) and make those require
an explicit human approval that a timeout *denies* rather than grants. A runnable version is
in [`starter-kit/authority/`](starter-kit/authority/): it classifies each action, denies the
consequential ones when nobody answers, and lets the routine work continue.

*Prevents: unreviewed consequential actions under degraded oversight; the model inventing
authority it was never delegated.*

### Phase 1: Conversational Design → Doc

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

**Anti-pattern.** One uniform context strategy for both modes: recency-forward autonomy lets
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

**Do this.** The durable output of Phase 1 is a **design document** (extracted from the
conversation, not the transcript) and a human approves it before it becomes a spec. Capture
by extraction (real decisions with their rationale), never by asking the model to "summarize
the chat."

**You've done it when.** There's an approved design doc a newcomer could read to understand
the decision and why, and that contains nothing no one actually decided.

**Anti-pattern.** Letting the chat log *be* the design record; or accepting a generated
summary that quietly invents a rationale nobody gave.

**Minimum viable today.** End each design session by writing a short decision doc (the model
may draft, you edit and approve); commit it to the corpus.

*Prevents: lost decisions; hallucinated rationale entering the record.*

### Phase 2: Doc → Structured Spec

The approved design doc becomes a **structured spec**: a task breakdown where every task
carries explicit, **checkable** acceptance criteria. This is the moment the output
distribution is narrowed, before a line of code is generated.

#### Write the spec before generating  ·  *buys L1 → L2*

**Do this.** Turn the approved design doc into a task breakdown where every task has explicit,
**checkable** acceptance criteria and names the **evidence** a gate will validate. The spec
narrows the output distribution before generation begins.

**You've done it when.** For every task, you can state how its output will be checked,
*before* a line is generated. If you can't, it's a prompt, not a spec.

**Anti-pattern.** "Build me X," with success defined after the fact by eyeballing the result.

**Minimum viable today.** Use [`starter-kit/spec/spec-template.md`](starter-kit/spec/spec-template.md);
require every task to carry at least one checkable criterion and one named artifact.

*Prevents: ambiguous targets; un-checkable "done"; scope drift.*

#### Gate the spec: a human approves before execution  ·  *buys L2 → L3*

**Do this.** The spec is itself gated: a human reviews and approves the human-readable
artifact before any code is generated against it. The most leveraged review you do is on
*intent*, not output.

**You've done it when.** No execution run starts against an unapproved spec, and approval is
recorded.

**Anti-pattern.** Jumping from a rough idea straight to autonomous execution, then finding
the spec was wrong after 40 files changed.

**Minimum viable today.** A required approval step (even a checkbox + a commit) between spec
and execution.

*Prevents: confidently executing the wrong thing; expensive late rework.*

#### Verify the machine ingested the plan you approved  ·  *buys L3*

**Do this.** Approval is not the last step before execution; ingestion is. After a human
approves the spec, the system parses it into what it will actually run, and you verify that
parse matches what was approved. The system reports its parse back (so many phases, so many
tasks, by name) and refuses loudly on anything unknown, duplicated, or ambiguous, rather than
silently executing a partial or altered reading. Run exactly the approved plan, nothing more
or less.

**You've done it when.** You can recognize your approved plan in what the system says it will
run, task by task, before any code is generated. A phase you approved that the parser dropped
is caught here, not discovered forty files later.

**Anti-pattern.** Silent partial acceptance: the human approves one representation, the
machine executes a different parse of it, and nothing flags the gap. Output gates cannot catch
this, because it is the system misreading intent on the way *in*, not the model diverging on
the way out.

**Minimum viable today.** After approval, have the system echo back a structured manifest of
what it parsed (phases and tasks, by name and count) for a human to confirm, and make it
refuse rather than guess on anything it cannot parse cleanly.
[`starter-kit/ingestion/`](starter-kit/ingestion/) does exactly that, and ships a spec with a
duplicated task id, a task whose criteria were lost, and a section the parser does not know,
so you can watch all three refuse instead of running short.

*Prevents: executing a silently altered or truncated version of the approved plan; dropped
tasks discovered late.*

### Phase 3: Execute the Spec

Implementation proceeds one task at a time, through a tight loop: **re-ground → generate →
gate → update corpus → next task.** We lead with the keystone, the independent gate, then
the rest of the loop.

#### Make the gate independent and tamper-resistant  ·  *buys L2 → L3*  ·  keystone

**Do this.** Validate evidence after the fact, with a checker the generating agent cannot run,
edit, or satisfy by assertion. The agent knows the contract it must meet (the acceptance
criteria live in the approved spec, so it can aim at them). What it never gets is the verifier
itself, the power to self-certify, or the specific held-out and adversarial fixtures the
checker uses. Public contract, private verifier. And for evidence the agent cannot forge, have
the gate *produce or observe* it (run the check itself, read output from a runner the agent
can't write to) rather than trust a log the agent submits: validating a submitted artifact
catches self-attestation, but not a forged artifact.

**You've done it when.** An agent that knows every acceptance criterion still cannot pass
without producing genuine evidence that it did the work. If restating the criteria, or
setting a "done" flag, is enough to pass, it's a rubric, not a gate.

**Looks like.** A single task, traced:

```
Spec      Task 3.2 "add bounded retry to the upload client". The acceptance criteria are
          public, in the approved spec the agent works from: retries bounded at 10,
          exponential backoff with jitter, no retry on 4xx (except 429), and a test that
          proves no_retry_on_4xx.

Gate      An independent checker renders the verdict against those criteria. The agent
          cannot run it, edit it, or pass it by asserting success. It runs the check itself
          against held-out cases the agent never saw, so passing means general correctness
          verified at the boundary, not a log the agent could have written.

Proof     The agent submits artifacts, not assurances:
              test_output: 14 passed, incl. test_no_retry_on_4xx
          The gate checks the artifact's *content*; a bare "done" does not pass.

Corpus    On a pass, a human promotes the decision and its evidence into the durable
          corpus, retrievable months later by a fresh session that never saw this task.
```

Two runnable gates are in [`starter-kit/gates/`](starter-kit/gates/), and the difference
between them is the lesson. `gate.py` validates a submitted evidence file plus its artifacts:
that gives you the evidence contract and the independent decision point, and it is forgeable,
because an agent that writes the artifact can write a convincing one. The directory ships a
forged submission that passes it. `gate_produce.py` hands the identical submission a failing
verdict, because the decisive check is named in the *spec* as a command the gate runs rather
than in the *evidence* as a path it reads. Same criteria, same submission; what changes is who
ran the check.

**Anti-pattern.** `human_approved: true` as a model-set boolean. Self-attestation is the #1
gaming vector: the model certifies its own work. (Hiding the requirements from the model is
the opposite mistake, and just as wrong. The model must know the contract to satisfy it; it
must not control the verifier that checks the evidence.)

**Minimum viable today.** You don't need a daemon. A pre-commit hook or CI step that runs a
gate script the model can't run or edit gets you the independent decision point today. For
evidence the model cannot forge, have that script produce the evidence itself (run the test,
read a trusted runner's output) rather than trusting a log the agent hands you. Copy
[`starter-kit/gates/gate_produce.py`](starter-kit/gates/gate_produce.py) and point it at your
own checks.

*Prevents: Goodhart / spec-gaming, silent self-certification.*

The other controls in the loop:

#### Re-ground at every step  ·  *buys L3 → L4*

**Do this.** Before each task's generation, retrieve the relevant project truth *again*
rather than trusting residue left in the window. Re-anchor every step; the channel is
engineered continuously, not configured once.

**You've done it when.** The number of steps between two retrievals of project truth is small,
ideally one. Every step in that gap is one where the model trusts window residue and error
compounds.

**Anti-pattern.** Front-loading all context at step 0 and letting it decay across a long run.

**Minimum viable today.** In your execution loop, retrieve the standards relevant to the
*current* task at the start of each task, not once at the top.

*Prevents: compounding drift; decisions made on stale or forgotten context.*

#### Keep durable memory deterministic  ·  *buys L2 → L3*

**Do this.** When memory must be condensed to fit, prefer **extraction** (selecting verbatim
content with its provenance) over generative summary. A summary that hallucinates poisons
every future retrieval; extraction can only omit, never invent.

**You've done it when.** Condensing the corpus can never produce a sentence no source ever
wrote. If it can, it's summarizing, not retaining.

**Anti-pattern.** Asking the model to "compact the history" into a generated summary that
becomes load-bearing memory, an unforced reliability risk the evidence runs against, not a
convenience.

**Minimum viable today.** When you trim memory, cut by selecting and keeping real excerpts
(with source links), not by generating a paraphrase.

*Prevents: hallucinated memory poisoning every downstream retrieval.*

#### Promote validated work into the corpus  ·  *buys L3*

**Do this.** A decision becomes durable corpus state when it passes its gate *and* a human
promotes it, with its evidence. Passing a gate makes work eligible; a human's judgment makes
it authoritative. The corpus grows through the work; uncaptured decisions are lost, and their
absence degrades future generations.

**You've done it when.** You can ask "where does last week's validated decision live?" and the
answer is the corpus, not the chat history, and you can name who promoted it.

**Durable is not the same as true.** The corpus faithfully preserves whatever enters it,
including decisions later proven wrong, requirements since superseded, and conflicting
sources. Durability is not truth. Carry provenance, mark superseded entries as superseded,
and resolve conflicts explicitly, so re-grounding retrieves current project truth and not
stale or contradicted content.

**Anti-pattern.** Decisions living only in PR threads, Slack, and chat logs, unreachable at
generation time. Or a corpus that accretes forever with no supersession, so retrieval keeps
resurfacing decisions the team has already overturned.

**Minimum viable today.** A git-tracked `/corpus` dir; on each gate pass, a human appends a
short decision record (what, why, evidence link) and marks any entry it supersedes. See
[`starter-kit/corpus/`](starter-kit/corpus/).

*Prevents: repeated mistakes; loss of hard-won decisions; ungrounded future work; stale truth
resurfacing.*

---

## Starter kit

Real, clonable artifacts, not pseudocode. Together they trace one coherent example (a
bounded-retry policy) across the whole loop:

- [`starter-kit/spec/spec-template.md`](starter-kit/spec/spec-template.md): a **spec
  skeleton** with checkable, per-task acceptance criteria.
- [`starter-kit/gates/`](starter-kit/gates/): two zero-dependency, runnable
  **independent-decision gates**. `gate.py` validates submitted evidence; `gate_produce.py`
  runs the check itself. A forged submission passes the first and fails the second, which is
  the whole argument in two commands.
- [`starter-kit/ingestion/`](starter-kit/ingestion/): a **plan-ingestion verifier** that prints
  the manifest it parsed (phases and tasks, by name and count) and refuses on a duplicated task
  id, missing criteria, or a section it does not recognize, rather than silently running short.
- [`starter-kit/authority/`](starter-kit/authority/): an **approval a timeout denies**, so
  degraded oversight narrows a run's authority instead of widening it.
- [`starter-kit/corpus/`](starter-kit/corpus/): a **deterministic corpus** layout, a
  git-tracked decision record and the standard it produces, the kind you retrieve when
  re-grounding the next task.
- [`starter-kit/assembly/`](starter-kit/assembly/): a **mode-aware assembly** sketch,
  recency-forward for conversation, pinned-goal for autonomy.

---

## Where Socium fits

This guide is the method. Doing it by hand is *laborious*: independent gates, deterministic
retention, and re-grounding at every step are real work to assemble and keep honest.
[Socium](https://socium.build) is the substrate being built to run this loop for you, end to
end, so the gates are independent and the corpus is deterministic by default instead of by
discipline.

This guide stands on its own. Socium aims to be the easy way to live by it.

---

## License

- **Prose / documentation:** [CC-BY-4.0](LICENSE-docs.md), use and adapt freely, with
  attribution.
- **Code / templates** (`starter-kit/`): [MIT](LICENSE).

Channel engineering is meant to be adopted. Attribution is all we ask.
