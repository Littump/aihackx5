# Planner v2: Classification, Insights, and a Portfolio of Challenges (start here)

> This is a plain-language proposal for the next version of the Domovoy challenge planner. It
> explains **why** we want to change it and **what** we propose, before any code. It is a
> companion to the precise design (`planner-v2-classification-insights.md`) and to the current
> system walkthrough (`ml-rework-explained.md`); the fixed set of behaviour signals, the rules
> for scoring and ranking them, and worked examples live in the taxonomy companion
> (`planner-v2-taxonomy-and-examples.md`). No prior knowledge is assumed — every new term is in
> the glossary below.
>
> Every number in the examples is a simulation assumption, not a real X5 figure.

---

## Part 0. A short glossary

Read this once and the rest is easy.

| Term | What it means, plainly |
|---|---|
| **Planner** | The cheap AI "analyst" that reads a summary about one shopper and plans that shopper's next challenge. |
| **Challenge** | A personal weekly task for the shopper: "visit three times this week", "buy milk again". Finish it, earn a reward and progress. |
| **Reward** | What the shopper gets for finishing. Two currencies: free game points (**XP**, always given) and spendable **X5 points** (money-equivalent, only when the budget allows). A challenge grants XP, or XP + points — never nothing. The AI picks the *form*; the code picks the *amount*. |
| **Classification ("name the buyer")** | The planner's own read of *who this shopper is right now*, written as a short buyer name plus one internal sentence — e.g. "Dormant but Formerly-Active Big-Basket Everyday Shopper". It is built from a fixed palette of keywords, so it is expressive but never made-up. |
| **Keyword** | One building block of the buyer name — one **lifecycle** word (rising / steady / cooling / dormant) plus optional **modifiers** (has_headroom, at_ceiling, large_basket, small_basket, broad, day_to_day, formerly_active, a lapsed category). Each keyword only applies if its measured number clears a bar. |
| **Price posture** | *How the shopper feels about discounts* — indifferent to promos, reacts only on a real need, or actively chases deals. One value, kept separate because it only decides **how much of the reward is X5 points**, not which challenge. |
| **Goal** | The one thing we choose to move this week: a **target** (only two exist — *visit more often* or *bigger basket*), the concrete **proxy** lever that moves it (e.g. re-buy a lapsed category, add a category), and a **direction** (increase / recover / sustain). The planner picks from this fixed set, never invents one. It is the bridge between "who they are" and "what we do". |
| **Derived signal** | A number the *code* computes from visit history before the AI sees it (e.g. "visiting 1.3x more than the month before"), so the AI reads a fact instead of guessing. The AI never does the arithmetic. |
| **Recency-weighted** | We compare the last four weeks against the four weeks before, so recent behaviour counts most and "recently" means the same window for every signal. |
| **Insight** | One small, named observation-and-goal: what we see now, what we want it to become, and one idea for how to get there. |
| **Definition of done (DoD)** | The "what we want it to become" part of an insight — a clear finish line, e.g. "buys milk again within a week". |
| **Hero / side challenge** | The one main challenge shown big to the shopper (hero), plus optional smaller extra tasks (side). |
| **Reasoning / thinking** | The model's free "scratch work" — its actual chain of thought — before it commits to a structured answer. |
| **Structured output** | A mode where the model must answer in a fixed shape (a filled-in form), not free text, so code can read it reliably. |
| **Single call** | One request to the AI that produces the whole plan — thinking, classification, insights, and challenges together — instead of several separate requests. |
| **Fallback** | The backup path: if the AI is unavailable or answers badly, plain rule-based code produces a valid plan so the product keeps working. |

---

## Part 1. Why change anything

Today's planner works, but it is a **black box that skips its own homework**.

- It never says *who it thinks the shopper is*. It jumps straight to "here is a challenge",
  with no stated read of the person. We cannot tell a good call from a lucky one.
- It does not actually **think**. Reasoning is switched off, so the only explanation we get is
  a single short sentence written after the fact.
- Its "insight" is just the input numbers we handed it, not anything the model concluded.
- Its one explanation is checked only by "does a number appear in the sentence" — which proves
  almost nothing about *why* this challenge fits this person.
- It returns **one** challenge. We cannot offer a main task plus a couple of lighter extras.

None of this is a targeting problem — targeting is already strong. It is a **transparency and
trust** problem: we cannot see the reasoning, cannot verify that each challenge follows from a
real observation, and cannot easily judge whether the planner understood the shopper.

---

## Part 2. What we propose, in two sentences

Make the planner **show its work in stages, in one AI call**: first think freely, then **name the
buyer** (a short buyer name built from fixed keywords), then pick the one thing to optimise this
week (the goal — one of two targets plus the proxy lever that moves it), then list a few named
insights that justify it, then propose one or more challenges — each tied to a specific insight —
and finally a short overall rationale that ties it all together.

Because every challenge points at a named insight, and the overall rationale must cover every
insight, the plan becomes **checkable**: we can confirm, automatically, that nothing was pulled
out of thin air.

---

## Part 3. The stages of one answer

The planner answers in a fixed order. Each stage must appear before the next, so the answer
reads like a short, honest analysis:

1. **Think** — free scratch work. The model weighs the numbers, considers a few readings of the
   shopper, and rules some out. This is the real thinking, kept visible.
2. **Name the buyer** — describe *who they are* as a short buyer name plus one internal sentence,
   built from a **fixed keyword palette**: one lifecycle word (rising / steady / cooling /
   dormant) and a few modifiers (room for one more trip, big/small basket, broad, a lapsed
   category, ...). Each keyword only applies if its number clears a bar, so the name is expressive
   but never invented. Separately, one **price posture** value — indifferent, selective, or
   deal-driven — which only sets the reward. The palette is in Part 3a.
3. **Set the goal** — pick the one thing to move this week: a **target** (only two exist — visit
   more often, or bigger basket), the **proxy** lever that moves it (re-buy a lapsed category, add
   a category, or none), and a direction (increase / recover / sustain). This is a quick
   statistical read of the keywords — "cooling but reachable → recover visits" or "at their visit
   ceiling but big baskets → grow the basket instead". It turns the description into one explicit,
   checkable decision before any insight is written.
4. **Insights** — two to four named observations that justify the goal, each in the same strict
   shape:
   - **name** — a short handle so we can refer to it later (e.g. `dairy_lapsed`).
   - **behaviour** — what we see now ("hasn't bought dairy in 16 days, though usually every 6").
   - **definition of done** — what we want instead ("buys dairy again within a week").
   - **strategy hint** — one idea to get there ("a small dairy re-buy task with a mid reward").
5. **Challenges** — one main (hero) challenge plus optional lighter (side) ones. **Each challenge
   names the insight it serves**, the hero's mechanic matches the goal, and each carries a
   **reward** (always XP, plus X5 points when the budget allows — never nothing), so its reason is
   explicit and verifiable.
6. **Overall rationale** — a short paragraph that must reference **all** the named insights and
   the goal, and note what to try next week.

A tiny, made-up example of the shape (illustrative, not real output):

```
think:      "On cadence but dairy fell off; still reachable, room for one more trip..."
classify:   keywords = [ steady, has_headroom, dairy_lapsed, day_to_day ]
            label = "Steady Everyday Regular with Room for One More Trip and a Lapsed Dairy Run"
            posture = value_selective,  ambiguous = false
goal:       target = visit_frequency,  proxy = lapsed_category_rebuy,  direction = recover
insights:   [ dairy_lapsed { behaviour, definition_of_done, strategy_hint },
              visit_headroom { ... } ]
challenges: [ HERO  -> serves "dairy_lapsed": re-buy dairy, +1 target, XP + points (medium)
              SIDE  -> serves "visit_headroom": one extra visit, XP only ]
overall:    "Recover visits via the lapsed dairy re-buy (a proxy that IS an extra trip) while
             nudging one more visit with XP; next week, drop the proxy if dairy completed."
```

---

## Part 3a. How we name the buyer, then choose a goal

The "name the buyer" and "goal" stages draw from a **fixed, closed vocabulary**, so the planner
cannot invent or randomise. The full palette, the rules, and worked examples are in
`planner-v2-taxonomy-and-examples.md`; here is the plain-language version.

**Name the buyer: a short name built from fixed keywords.** No opaque box, no ranked list — the
planner writes a short, human-readable buyer name plus one internal sentence, assembled from a
**closed keyword palette**. Each keyword is a fact with a bar: it only applies if its
**derived, recency-weighted** number (last four weeks vs the four before) clears a threshold, so
the read is expressive yet grounded. Two kinds of keyword:

- **Lifecycle — pick exactly one** (four readings of the *same* recency number, so only one is
  ever true):
  - **Rising** — visiting more lately than before.
  - **Steady** — clockwork routine, on their usual cadence.
  - **Cooling** — starting to slip off their rhythm, but still reachable.
  - **Dormant** — absent well past their usual gap, nearly lost.
- **Modifiers — add a few that fit** (they make the name specific): *formerly active* (used to
  come more), *room for one more trip*, *at their ceiling*, *big basket* / *small basket*,
  *broad* (many categories), *day-to-day* (staple-led), and *a lapsed category* (a usual category
  a full cycle overdue).

So instead of forcing a shopper into "heavy loyalist" or "light / occasional", we name them:
e.g. *"At-Ceiling Steady Loyalist with Big Broad Baskets"* for a big weekly regular, or *"Dormant
but Formerly-Active Big-Basket Everyday Shopper"* for the classic win-back.

Price posture is kept **separate** and is a single value, because it answers a different question
— *how do they feel about discounts?* — and only sets how much of the reward is X5 points, never
the challenge:

- **Promo-immune** — routine beats discounts; reward with XP only, not points.
- **Value-selective** — reacts only when a discount lands on a real, timely need; XP plus a
  mid-size points reward, used sparingly.
- **Deal-driven** — genuinely chases value; XP plus a stronger points reward is justified,
  especially to win them back.

**Goal: the one thing to optimise this week.** Naming the buyer is not the same as deciding what
to do about it. The goal stage makes that one decision — a **target**, a **proxy** lever, and a
**direction** — read straight off the keywords:

- **Targets — only two, because those are the two things the economics pays for:** *visit
  frequency* (how often they come — the primary lever, since the reward budget is driven by extra
  trips) and *basket value* (spend per trip — the secondary lever, the only one left when a stable
  buyer has no room to visit more). The planner never adds a third.
- **Proxies — how the target is actually hit:** re-buy a lapsed category (an extra trip → serves
  *visit frequency*), add a category / pairing (bigger spend → serves *basket value*), steer
  toward a higher-margin category (→ *basket value*), or *none* (move the target head-on). A
  lapsed category or extra breadth is a **proxy, never a target** — a common past mistake this
  fixes.
- **Directions:** *increase* (push up — there's headroom or rising momentum), *recover* (reverse
  a decline — cooling, dormant, or a lapsed category), *sustain* (hold a strong routine — reward
  with XP only, no points; a "streak" is an XP/league mechanic, not a challenge).

The choice follows the keywords: cooling/dormant → recover visit frequency (with a lapsed-category
re-buy as the proxy if one exists); rising or room-to-visit → increase visit frequency; a steady
shopper already at their visit ceiling but with big baskets → increase basket value via adding a
category instead. This is exactly the "maybe not boost frequency but grow the basket, because
they're a stable buyer" call, made explicit. The goal then picks the challenge's mechanic, and the
insights that follow must justify hitting it.

Why keep name, decide, and posture apart: the questions — *who are they?*, *what should we move?*,
and *how do they feel about discounts?* — are independent, so we keep them as separate, checkable
decisions instead of one overloaded label.

---

## Part 4. Why each stage earns its place

- **Classification** answers "did the planner understand the shopper?" — the question we cannot
  ask today. A name built from fixed keywords is expressive without fake precision; real shoppers
  are a mix, and the name captures that.
- **The goal** forces one explicit choice — *what are we optimising?* — instead of letting the
  challenge imply it. With only two targets plus a proxy, it is read from the keywords, so it is
  checkable, and it stops the planner from, say, pushing more visits at someone already at their
  ceiling.
- **Insights with a definition of done** turn vague hunches into **measurable goals**. The DoD
  is also what tells us later whether the challenge actually moved the needle, not just paid for
  something the shopper would have bought anyway.
- **Challenges tied to a named insight** make every task **traceable to a reason**. No orphan
  challenges, no orphan insights.
- **An overall rationale covering all insights** forces the plan to be coherent — every
  observation is either acted on or explicitly folded into the strategy.
- **Real thinking first** improves the quality of everything after it: the model reasons before
  it commits, instead of blurting an answer.

---

## Part 5. One call, not many

We deliberately keep this a **single AI call**, not a pipeline of separate calls (one to
classify, one for insights, one to plan). Reasons:

- **Cheaper and faster.** One request instead of three or four; the planner model is the cheap
  one, and latency stays low.
- **More coherent.** The challenges are chosen in the *same breath* as the classification and
  insights that justify them, so they cannot drift apart.
- **Simpler to run and trace.** One request, one record, one place to inspect.

The trick that makes one call enough: the answer's **fixed order of sections** walks the model
through the stages by itself. It thinks first, then classifies, then lists insights, then
plans — all inside one structured response. We do not need separate calls to enforce the order.

---

## Part 6. What people actually see

- **The shopper** sees, as today, one clear main challenge with a friendly "why this is for
  you". Optionally, a couple of lighter side tasks. They never see the internal stages.
- **The product manager / reviewer** sees the full short analysis per shopper — the
  classification, the named insights, and which challenge serves which insight — in the trace
  (Langfuse). It reads like a one-screen analyst note, so a human can judge it without reading
  code.

---

## Part 7. How we know it works

Alongside the existing (expensive) simulation, we add a **small, fast check focused only on
classification** across shopper types:

- Take a handful of shoppers — a few from each segment (steady regulars, light, heavy, dormant).
- Run **only the planner** on each (no shopper simulation), so it is cheap and quick — minutes,
  not an hour.
- Check, automatically, that: the planner produced a real ranked classification; the **top
  signal** matches the shopper's actual behaviour; it did not just copy the segment we handed in;
  and every challenge points at a real insight while the overall rationale covers them all.

This answers exactly one question — "does the planner read shoppers' behaviour, and correctly?" —
and is separate from the money-focused simulation we already run.

---

## Part 8. Honest risks, and how we handle them

- **"It's complicated" hedging.** The planner could pile on keywords for everyone. The palette
  forces exactly one lifecycle word and only lets a modifier in when its number clears the bar, so
  a long name is never free; "ambiguous" is flagged only on a real lifecycle boundary.
- **Too many insights.** We limit insights to two-to-four, and each must cite a real number.
- **Blowing the budget on rewards.** X5 points are budget-gated by code (the weekly points cap and
  the 40% incremental-margin rule), and a promo-immune shopper gets XP only. XP is free, so a
  challenge always pays something without ever risking the money budget.
- **Longer answers cost more.** Thinking plus insights plus several challenges is more text; the
  planner model is cheap, but we budget the length so it stays reliable.
- **A buyer name that just echoes the input label.** The check rewards reading real behaviour
  (cooling, a lapsed category, room to visit more), not repeating the segment we gave it.

---

## Part 9. What changes versus today, in one line each

- The planner now **thinks out loud** before answering (reasoning turned back on).
- It **names the buyer** — a short buyer name built from a fixed keyword palette (one lifecycle
  word + a few modifiers) plus one **price posture**, instead of an opaque label or a ranked list.
- It **sets one goal** — one of **two** targets (visit frequency or basket value), the **proxy**
  lever that moves it, and a direction; a lapsed category or breadth is a proxy, never a target.
- It picks a **reward** in two currencies — always XP, plus X5 points when the budget allows —
  so a challenge is never worthless and never blows the money budget.
- It produces **named insights** (see / want / how) that justify the goal, not just echoed numbers.
- It can return **several challenges**, each tied to a specific insight.
- Its overall rationale must **cover every insight**, and code verifies the links.
- A new **small classification check** tells us quickly whether the read of the shopper is right.
- All of it happens in **one AI call**.

---

## Where to go next

- The precise schema, validator rules, and file-by-file plan — `planner-v2-classification-insights.md`.
- The full keyword palette, the two-target/proxy goal rule, the two-currency reward rule, the insight catalogue, and worked examples — `planner-v2-taxonomy-and-examples.md`.
- How the current planner works today — `ml-rework-explained.md`.
- The metrics behind the simulation — `metrics-explained.md`.
- The synthetic shopper and traces — `actor-and-tracing.md`.
