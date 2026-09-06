# Planner v2: Buyer-Naming Taxonomy, Goal & Reward Rules, Insight Library, and Few-Shots

> Source of truth for **what the v2 planner may say**: the closed keyword palette it uses to
> **name the buyer**, the rules for composing that name, the two-target + proxy goal rule, the
> two-currency reward rule, the fixed catalogue of insight kinds, and the few-shot examples. The
> few-shots and enums here are meant to be embedded, close to verbatim, into
> `dev/backend/app/ml/prompts/planner_system.md` so the model instantiates from a closed
> vocabulary instead of inventing labels.
>
> Everything is grounded in signals that already exist in `PlannerInput`
> (`app/ml/schemas.py`) and thresholds that already exist in `app/ml/config.py` and
> `app/ml/rules.py`. Numbers are simulation assumptions, not real X5 figures.

---

## Part 0. Why these categories (research grounding)

The taxonomy is not invented; it is the intersection of three well-worn frameworks, narrowed to
what our signals can actually support.

- **RFM (Recency / Frequency / Monetary) 11-segment model.** The industry-standard naming —
  Champions, Loyal, Potential Loyalist, Need Attention, At Risk, Can't Lose Them, Hibernating,
  Lost — maps cleanly onto our `frequency_per_week` (F), `recency_days` (R), and `avg_basket`
  (M proxy). We reuse the *shapes*, not the 5x5x5 scoring.
  (rfm package / MetricGate: https://metricgate.com/docs/rfm-segmentation ;
  https://umbrex.com/resources/frameworks/strategy-frameworks/rfm-segmentation)
- **Customer lifecycle (Acquire → Onboard → Develop → Retain → Win-Back).** Gives the
  engagement *states* and the transition triggers: an engagement drop → "at risk", a longer
  inactivity window → "lapsed / win-back". This is where our `churn_risk` (`none / elevated /
  high`) comes from conceptually.
  (https://umbrex.com/resources/frameworks/marketing-frameworks/customer-lifecycle-framework-acquire-onboard-develop-retain-win-back ;
  https://crmknowledgebase.com/foundations/lifecycle-mapping)
- **Grocery behavioural archetypes + deal sensitivity.** The price-posture axis: "Mission
  Buyer" (low price sensitivity, habit-driven) vs "Value Hunter" (high price sensitivity,
  deal-driven), and the "chore" habitual shopper who is unresponsive to promotions. This is our
  price-posture read and matches the existing `deal_attitude` in `profiles.py`
  (`promo_skeptic / selective / deal_seeker`). Attitudinal loyalty responds to *personalised*
  price promotions, not generic blasts — which is exactly the planner's job.
  (https://measureprotocol.com/insights/online-grocery-shopper-archetypes ;
  https://segmentationstudyguide.com/market-segmentation-example-grocery-shoppers)
- **Gamified loyalty / next-best-action.** Time-bound missions tied to a visit window ("visit
  twice this week by Sunday") are the mechanic that actually lifts frequency; NBA says optimise
  the *best* intervention, not the biggest discount; personalised offers redeem far better than
  generic ones, and reward fatigue/abuse is the main failure mode. This justifies the one-money-
  reward guardrail and the deadweight-avoidance insight below.
  (https://neoday.com/blog/gamified-loyalty-programs-retail ;
  https://cxforge.com/blog/ai-loyalty-personalization-next-best-action)

### Why a composed, evidence-scored read, not one hard label (2026 practice)

Contemporary RFM / CDP practice does not drop a shopper into one exclusive box. It **scores** each
behaviour relative to the base (quintiles / percentiles, not fixed thresholds), weights
**recency** most heavily, keeps the **observation window** consistent across metrics, and layers a
*small* set of behavioural signals on top of the RFM base — pushing past ~4 tiers kills
actionability. Next-best-action then **ranks** the resulting propensities and acts on the top one
instead of committing to a single label.
(digitalapplied 2026 — layered RFM→behavioural→predictive stack, 4-tier ceiling:
https://digitalapplied.com/blog/customer-segmentation-2026-rfm-behavioral-predictive-framework ;
useamp / metricgate — quintile scoring, recency carries the most weight, same window for F & M:
https://useamp.com/blog/rfm-analysis , https://app.metricgate.com/blogs/rfm-segmentation-for-marketing ;
polaranalytics — "score a customer, get the play": https://polaranalytics.com/post/rfm-analysis-for-shopify)

Design consequence — the planner reads the shopper in three plain steps, and every step serves
**one product goal** (§0.1):

1. **Name the buyer** — `classification`: a short buyer name plus a one-line internal description
   that captures who they are as a shopper, composed from a **closed keyword palette** (§2.1) and
   backed by the derived metrics. Not one hard box and not a ranked enum — a human-readable read
   like *"Dormant, formerly-active, big-basket, day-to-day shopper"*, assembled from fixed
   keywords so it is expressive yet never random. Plus `posture`: one price-attitude value (§2.2).
2. **Pick the goal** — `goal`: the one business feature to move, a direction, and the concrete
   proxy lever (§2.4). There are only **two targets** — `visit_frequency` (primary) and
   `basket_value` (secondary) — because those are the two things the product economics actually
   pays for. A lapsed category, extra breadth, or a high-margin category is a **proxy** that serves
   one of the two targets, never a target of its own.
3. **Ground it** — `insights`: factual, named observations that justify hitting that goal, each
   tied to a real number.

Naming the buyer (describe) stays apart from picking the goal (decide): the description never
pretends to be the plan, and the goal is one explicit, checkable choice. A shopper gets one buyer
`classification` (name + keywords + description), exactly one `posture`, and exactly one `goal`
(target + proxy + direction).

### 0.1. Grounding in product vision (why only two targets)

The target set is not free — it is dictated by what «Домовой» is for and by how the reward budget
is computed, so the planner optimises what the business actually pays for, not an academic list.

- **Product goal (PRD §1, demo §1).** «Домовой» exists to *raise purchase frequency without
  growing the promo budget or eroding margin per member*. The core segment is the 3–7-buys-a-month
  shopper who still has headroom for one more trip and sits just below the "N buys per period"
  threshold. So the **primary** target is `visit_frequency`.
- **Economics (PRD §7.4, `economics.py`).** The reward budget is
  `incremental_purchases × avg_basket × contribution_margin × 0.40`. Frequency (incremental
  purchases) is the dominant term; `avg_basket` is the multiplier. When a shopper has no frequency
  headroom (a stable, at-ceiling buyer), the only remaining lever on that budget is **basket
  value** — so `basket_value` is the **secondary** target.
- **Everything else is a proxy.** A lapsed-category re-buy, an extra category, or a high-margin
  category push are *tactics* that move one of the two targets: a category re-buy is an
  incremental trip (→ `visit_frequency`); adding or up-weighting a category grows spend per trip
  (→ `basket_value`). They are chosen as levers, not optimised as ends. (Per-category margin is a
  flat `CONTRIBUTION_MARGIN = 0.15` today; when a real per-category margin lands, "steer
  `basket_value` toward high-margin categories" plugs in here without adding a new target.)

---

## Part 1. The signal vocabulary (what the model may cite)

The planner may only reason from these fields (already computed in `app/ml/insight.py`). Every
`evidence` / `evidence_metric` must reference one of them by its real value.

| Signal | Source | Meaning | Key thresholds (grounded) |
|---|---|---|---|
| `frequency_per_week` | `PlannerFeatures` | visits per week | headroom if `< 6.0` (`_FREQUENCY_HEADROOM_MAX`); heavy ≈ `>= 2.2`, light ≈ `<= 0.8` |
| `recency_days` | `PlannerFeatures` | days since last visit | active if `<= 21` (`_RECENCY_MAX_DAYS`) |
| `cadence_days` | `PlannerFeatures` | avg gap between visits | reference for churn ratio |
| `churn_risk` | `PlannerFeatures` | derived from `recency/cadence` | `elevated` if ratio `> 1.8`, `high` if `> 2.6` (`config`) |
| `baseline_visits` | `PlannerFeatures` | usual weekly visits | target corridor base |
| `avg_basket` | `PlannerFeatures` | avg spend / visit (M proxy) | "large basket" ≈ `>= ~900` (heavy band) |
| `promo_sensitivity` | `PlannerFeatures` | 0..1 responsiveness to money | `< 0.35` immune, `0.35–0.62` selective, `>= 0.62` deal-driven (`profiles` cuts) |
| `segment` | `PlannerUser` | coarse input bucket | `regular_mid / light / heavy / dormant` |
| category `days_overdue` | `CategoryTimeseries` | how far past its own cadence | "lapsed" if `>= cadence_days` (one full cycle) |
| category `share` | `CategoryTimeseries` | fraction of visits with this cat | eligible if `>= 0.10` (`_CATEGORY_MIN_SHARE`); "staple" if very high |
| category `visits` | `CategoryTimeseries` | visits touching this cat | eligible if `>= 3` (`_CATEGORY_MIN_VISITS`) |
| `previous_plans` | `PreviousPlan[]` | last challenges + status/used | continuity |

Target corridor (from `rules.target_corridor`): `baseline+1 .. baseline+2` (a small step, never a
round jump). Reward amount is always computed by code, never by the model.

---

### Part 1b. Derived signals (computed by code, handed to the model)

The raw fields above are thin, so the model would be *guessing*. To let it **decide**, the insight
builder (`app/ml/insight.py`) computes a few **derived, recency-aware** signals from the same
visit history and adds them to `PlannerFeatures`. Code computes every number (the model never does
arithmetic); the model only reads them and ranks the behaviour signals. Constants are simulation
assumptions and live in `config.py` / `game_rules.py`, never in a prompt.

Windows: **recent = last 28 days**, **prior = the 28 days before that** (equal width, so momentum
is comparable — the "same observation window" rule).

| Derived signal | Formula (from visit history) | Reads as |
|---|---|---|
| `visit_momentum` | `freq_recent / max(freq_prior, 0.25)` | `> 1.15` speeding up, `< 0.85` slowing down |
| `overdue_ratio` | `recency_days / max(cadence_days, 1)` | `<= 1.1` on-time, `1.2–2.6` cooling, `> 2.6` dormant (same cuts as `churn_risk`) |
| `cadence_regularity` | `1 - min(1, stdev(gaps)/mean(gaps))` | near `1` = clockwork routine, near `0` = erratic |
| `visit_headroom_ratio` | `clamp((VISIT_CEILING - frequency_per_week)/VISIT_CEILING, 0, 1)`, only if `recency_days <= 21` | `>= 0.3` = real room for one more trip |
| `basket_index` | `avg_basket / BASKET_REFERENCE` | `>= 1.2` = large basket vs base (`M` proxy) |
| `category_breadth` | count of categories with `share >= 0.10` | `>= 3` = broad shopper (room to deepen) |
| `top_category_overdue_ratio` | max over non-staple owned cats (`share>=0.10`, `visits>=3`) of `(days_overdue + cadence)/cadence`; else `1` | `>= 2` = a real category is a full cycle overdue |

`VISIT_CEILING` (a realistic "one more trip" ceiling, ~`3.0`/wk) and `BASKET_REFERENCE` (base-mean
basket, ~`600₽`) are tunable constants, not model output. These seven signals are exactly what the
scoring rules in Part 3 consume, so the LLM and the deterministic rule-fallback rank identically.

---

## Part 2. Classification, posture, goal, reward

### 2.1. Name the buyer (keyword palette + one-line description)

The planner does **not** emit a hard category or a ranked enum. It **names the buyer**: a short,
human-readable label plus one internal sentence, composed from the **closed keyword palette**
below. The palette is what keeps the read expressive but grounded — the model may use only these
keywords, and each keyword has a metric bar (Part 1b) so the LLM and the rule-fallback pick the
same tags. That is the anti-hallucination guarantee: rich phrasing, fixed building blocks.

**Classification output (per shopper):**

- `keywords` — 2..5 closed tags from the palette, the lifecycle tag first (machine-checkable).
- `label` — a short Title-Case buyer name, composed **only** from those keywords, e.g.
  "Dormant but Formerly-Active Big-Basket Everyday Shopper".
- `description` — one internal sentence capturing them as a buyer, grounded in real numbers.
- `evidence` — the metric behind each non-obvious keyword (e.g. `overdue_ratio=2.83`).
- `posture` — one price-attitude value (Part 2.2), kept separate from the name.

**Lifecycle / trajectory — pick exactly ONE** (the four are readings of the same recency metric,
so only one is ever true; the number decides, no manual rule):

| keyword | plain meaning | measured by | picked when |
|---|---|---|---|
| `rising` | visiting more lately than before | `visit_momentum` | `> 1.15` |
| `steady` | clockwork routine, on cadence | `cadence_regularity` + `overdue_ratio` | regularity `>= 0.6` and `overdue_ratio <= 1.1` |
| `cooling` | slipping off cadence, still reachable | `overdue_ratio` | `1.2 < ratio <= 2.6` |
| `dormant` | long gap, near-lost | `overdue_ratio` / `recency_days` | `ratio > 2.6` or very high `recency` |

**Modifiers — add 0..4 that clear their bar** (these make the name specific; each must be backed
by its metric in `evidence`):

| keyword | plain meaning | measured by | added when |
|---|---|---|---|
| `formerly_active` | used to come more than now | `visit_momentum` | `<= 0.7` (recent pace well below prior) |
| `has_headroom` | room for one more trip this week | `visit_headroom_ratio` (+ active recency) | `>= 0.3` and `recency <= 21` |
| `at_ceiling` | already near their own visit ceiling | `visit_headroom_ratio` | `< 0.15` |
| `large_basket` | big baskets vs base | `basket_index` | `>= 1.2` |
| `small_basket` | small baskets vs base | `basket_index` | `<= 0.7` |
| `broad` | shops many categories per trip | `category_breadth` | `>= 3` |
| `day_to_day` | staple-led, every-trip essentials | staple category `share` | a category with very high `share` (bought every trip) |
| `<category>_lapsed` | one usual category a full cycle overdue | `top_category_overdue_ratio` | `>= 2` (this is the proxy hook, Part 2.4) |

The `label` is those keywords phrased naturally; nothing outside the palette may appear in it. The
old flat types fall out as keyword combos (nothing lost): `heavy_loyalist` = `steady` +
`large_basket` + `broad` + `at_ceiling`; `habitual_regular` = `steady`; `winback_at_risk` =
`cooling`; `dormant_reactivation` = `dormant` (+ `formerly_active`); `light_occasional` =
`steady`/`rising` + `small_basket`. No "too big / too small / overlapping" boxes — just a name.

### 2.2. Price posture (one value, sets the reward — not part of the buyer name)

Posture is a *separate*, single read from `promo_sensitivity`. It is never part of the buyer name
and never picks the challenge; it only sets the **reward mix** — whether X5 points are attached
and how strong (the reward model is Part 2.5).

| `posture` | Grocery analog | Meaning | Trigger | Implied reward mix (Part 2.5) |
|---|---|---|---|---|
| `promo_immune` | Mission Buyer / "chore" habitual | Routine beats discounts | `promo_sensitivity < 0.35` | XP only (`points_level=none`) — cash on a trip they'd make anyway is deadweight |
| `value_selective` | Selective / situational | Reacts only on a real, timely need | `0.35 <= promo_sensitivity < 0.62` | XP + `points_level` up to `medium`, only when it hits a real need |
| `deal_driven` | Value Hunter / deal-seeker | Chases genuine value | `promo_sensitivity >= 0.62` | XP + `points_level` up to `high`, especially to win back |

### 2.3. Naming rule (anti-hedging, anti-randomising)

- Exactly **one** lifecycle keyword (the four are mutually exclusive readings of the recency
  metric — the number decides, no manual rule).
- **0..4 modifiers**, each included only if its metric clears the "added when" bar; a modifier
  below the bar is *omitted*, never padded in for flavour.
- `label` and `description` may use **only** the chosen keywords — no free adjectives, no invented
  types. `evidence` must cite the metric behind each non-lifecycle keyword.
- `is_ambiguous = true` only when the shopper sits on a lifecycle boundary (e.g. `overdue_ratio`
  near `1.2` or `2.6`). It is not a licence to stack keywords.
- Posture is chosen separately (Part 2.2), always exactly one, and never part of the name.

### 2.4. Goal setup (the stage between classify and insights)

Reading the behaviour is not the same as deciding what to do about it. After classification and
**before** any factual insight, the planner sets **one goal**: the single shopper feature to move
this week, plus a direction. This is a purely statistical pre-analysis over the derived metrics —
"we see frequency cooling and they're still reachable → recover frequency"; or "frequency is at
the ceiling but baskets are large and they're loyal → grow the basket instead". It is the
next-best-action choice, made explicit and checkable.

**There are only two targets — the two things the economics actually pays for (§0.1).** The
planner picks **exactly one** `goal.target`, and it is one of just two values. Everything else a
challenge might do (win back a lapsed category, add a category, steer toward a high-margin
category) is a **proxy lever** that *serves* one of those two targets — it is never a target of
its own. This is the fix for the old "closed universe of four": `basket_breadth` and
`category_reengagement` were never things the budget pays for directly; they are tactics.

| `goal.target` (enum) | Priority | Shopper feature it moves | Why it is a real target (economics) | Measured by (derived metric) | Valid directions | Base mechanic (`ChallengeType`) |
|---|---|---|---|---|---|---|
| `visit_frequency` | primary | how often they shop | dominant term of the reward budget — `incremental_purchases` (PRD §7.4, `economics.py`) | `visit_momentum`, `overdue_ratio`, `visit_headroom_ratio` | `increase` / `recover` / `sustain` | `frequency` |
| `basket_value` | secondary | spend per trip | the multiplier `avg_basket`; the only lever left when a stable buyer has no frequency headroom | `basket_index` | `increase` / `sustain` | `basket` |

**Proxy levers — how a target is actually hit this week.** A proxy is the concrete tactic; it does
not replace the target, it names the mechanic that moves it. The planner picks one from this fixed
set (or `none`) and must state which target it serves.

| `goal.proxy` (enum) | Serves target | What it does | Mechanic (`ChallengeType`) |
|---|---|---|---|
| `lapsed_category_rebuy` | `visit_frequency` | win back a specific overdue category — a timely incremental trip | `replenishment` (or `category`) on that category |
| `add_category` | `basket_value` | grow spend per trip by adding a complementary category / pairing | `collection` |
| `high_margin_category` | `basket_value` | steer the basket toward a higher-margin category (future: per-category margin) | `category` / `collection` |
| `none` | either | move the target head-on, no category tactic | `frequency` (visits) or `basket` (rubles) |

`category_reengagement` **is not a target — it is the `lapsed_category_rebuy` proxy** serving
`visit_frequency` (the re-buy is an extra trip). Likewise "breadth" is the `add_category` proxy
serving `basket_value`, and category-margin steering is the `high_margin_category` proxy —
available today as a lever, honest that per-category margin is a flat `CONTRIBUTION_MARGIN = 0.15`
until real margins land (§0.1). `streak` is **not** a proxy and **not** a challenge: holding a
routine is an XP/league mechanic (`XP_STREAK_4W`), delivered as `sustain` on `visit_frequency`
with XP only, never as a challenge type.

**Goal direction** (`goal.direction`, closed enum of exactly three): `increase` (push the target
up — there is headroom or rising momentum), `recover` (reverse a decline — cooling / dormant / a
lapsed category), `sustain` (hold a strong current level — reward with XP only, no points). Valid
pairings: `visit_frequency` → `increase` / `recover` / `sustain`; `basket_value` → `increase` /
`sustain`.

**Selection rule (from the buyer keywords, deterministic so the fallback matches):**

1. Lifecycle `dormant` or `cooling` → `target=visit_frequency`, `direction=recover`. Proxy =
   `lapsed_category_rebuy` if a `<category>_lapsed` keyword is present, else `none`.
2. Else `<category>_lapsed` present (on a `rising`/`steady` buyer) → `target=visit_frequency`,
   `direction=recover`, `proxy=lapsed_category_rebuy`.
3. Else `rising` or `has_headroom` clears its bar → `target=visit_frequency`,
   `direction=increase`, `proxy=none`.
4. Else `at_ceiling` with `large_basket`/`broad` → `target=basket_value`, `direction=increase`;
   `proxy=add_category` when the play is a new category/pairing (`collection`), else `none`
   (a bigger single `basket`).
5. Else `steady` with nothing to push → `target=visit_frequency`, `direction=sustain`,
   `proxy=none` (XP only, no challenge-type streak).

`goal.rationale` must cite the metric behind the chosen target and proxy (e.g. `overdue_ratio=1.8`,
`visit_headroom_ratio=0.57`, `basket_index=1.83`, `top_category_overdue_ratio=2.67`). Posture is
orthogonal: it does not change the target or proxy, only the **reward mix** (§2.5) attached to the
mechanic they imply.

### 2.5. Reward (two currencies, never none)

A challenge is pointless if it grants nothing, so **every challenge grants a reward** — one of two
currencies, or both, but never neither. This mirrors the product's own two reward rails
(`domain-rules.md` §7, `game_rules.py`): free game **XP** (always on) and spendable **X5 points**
(budget-gated). The planner picks the *shape* (which currency, ordinal strength); **code computes
every amount** — the LLM never sets a number.

| Reward field | Currency | Values | Rule |
|---|---|---|---|
| `reward.xp_level` | XP (game points) | `low` / `medium` / `high` | **Always present.** Any completed weekly challenge earns XP (`XP_CHALLENGE = 50` base); XP is free, off-budget, never `none`. |
| `reward.points_level` | X5 points (money-equiv) | `none` / `low` / `medium` / `high` | Budget-gated: attached only when posture and economics justify it. `low` maps to ≥ `REWARD_POINTS_MIN = 30`; capped by `REWARD_POINTS_MAX_WEEKLY = 150` and the 40 % incremental-margin rule (`REWARD_SHARE_MAX`). Below the min → `none` (XP still stands). |

**Never-none invariant:** `xp_level` is always one of the three, so a challenge always pays at
least XP. In practice a challenge is either **XP-only** (`points_level = none`) or **XP + points**.
Points-only is impossible (XP is the base rail). This replaces the old `reward_kind`
(`promo`/`ladder`/`none`) + single `reward_level` shape — see the schema-change note in Part 6.

**Posture → reward mix** (§2.2 drives points, not the target):

- `promo_immune` → XP only (`points_level = none`): cash on a trip they'd make anyway is deadweight.
- `value_selective` → XP + `points_level` up to `medium`, only when the challenge hits a real,
  timely need.
- `deal_driven` → XP + `points_level` up to `high`, especially to win back a dormant buyer.

---

## Part 3. How to name the buyer and pick the goal

The model — and the rule-fallback (`rules.py`), identically — derives the keywords, composes the
name, then picks the goal like this. No ML: the derived metrics from Part 1b map monotonically to
the keyword bars, so LLM and code agree.

**Derive the buyer keywords (§2.1):**

1. **One lifecycle keyword.** `overdue_ratio > 2.6` (or very high `recency`) → `dormant`;
   `1.2 < ratio <= 2.6` → `cooling`; else `visit_momentum > 1.15` → `rising`; else `steady`.
   Exactly one is ever true — the number decides.
2. **Add 0..4 modifiers** whose metric clears its "added when" bar (§2.1): `formerly_active`,
   `has_headroom`, `at_ceiling`, `large_basket`, `small_basket`, `broad`, `day_to_day`,
   `<category>_lapsed`. A modifier below the bar is omitted, never padded in.
3. `is_ambiguous = true` only when the shopper sits on a lifecycle boundary (`overdue_ratio` near
   `1.2` or `2.6`) — not a licence to stack keywords.

**Compose the label + description:** phrase the chosen keywords naturally into a Title-Case buyer
name and one internal sentence, using **only** those keywords; cite the metric behind each
non-lifecycle keyword in `evidence`.

**Pick the goal (Part 2.4 selection rule):** from the keywords choose exactly one `goal.target`
(one of the two), one `goal.proxy` (serving that target, or `none`), and one `goal.direction`; cite
the deciding metric in `goal.rationale`.

**Pick the reward (Part 2.5):** always set `xp_level`; set `points_level` from posture and the
economics budget (`none` when unjustified). Code computes amounts.

**Posture** comes straight from `promo_sensitivity` (Part 2.2). It never enters the keywords or the
goal; it only sets the reward mix.

**Segment → plausible buyer keywords** (a sanity check for the eval, not a hard rule — behaviour
may legitimately override the coarse input bucket):

| `segment` | plausible lifecycle + modifiers |
|---|---|
| `regular_mid` | `steady` / `rising` / `cooling`; `has_headroom`, `<category>_lapsed` |
| `light` | `rising` / `steady`; `small_basket`, `has_headroom` |
| `heavy` | `steady`; `large_basket`, `broad`, `at_ceiling` |
| `dormant` | `dormant` / `cooling`; `formerly_active` |

---

## Part 4. Insight library (closed set of kinds)

To stop the model from inventing or randomising insights, it must instantiate each insight from
one of these **fixed kinds**. The `name` follows the kind's convention; `behaviour`, `dod`,
`strategy_hint` follow the template with real numbers substituted; `evidence_metric` must be a
real value from Part 1 / Part 1b. Pick 2..4 kinds; do not repeat a kind. Each **action** kind
maps to one Part 2.1 buyer keyword (its trigger cites that keyword's metric) and serves the chosen
`goal` (target via its proxy), so name → goal → insights line up: `momentum_ride`↔`rising`,
`streak_continuity`↔`steady` (support only), `churn_drift`↔`cooling`, `dormant_gap`↔`dormant`,
`visit_headroom`↔`has_headroom`, `basket_depth`↔`large_basket`/`broad`,
`lapsed_category`↔`<category>_lapsed` (the `lapsed_category_rebuy` proxy).
The insight that carries the goal's own metric should be the hero challenge's `insight_ref`.

| Kind | `name` convention | Trigger | `behaviour` template | `dod` (definition of done) | `strategy_hint` | Typical mechanic / reward |
|---|---|---|---|---|---|---|
| **lapsed_category** | `<category>_lapsed` | `top_category_overdue_ratio >= 2` on that cat (`share>=0.10`, `visits>=3`, not staple) | "buys `<cat>` every ~`<cadence>`d but none for `<recency-in-cat>`d" | "re-buys `<cat>` within a week" | "replenishment/category on `<cat>`, target 1" | `replenishment` / posture reward |
| **momentum_ride** | `momentum_ride` | `visit_momentum > 1.15` (speeding up) | "visiting ~`<freq_recent>`/wk lately vs `<freq_prior>` before — rising" | "hold the higher pace one more week" | "frequency stretch, small reward" | `frequency` / low |
| **visit_headroom** | `visit_headroom` | `visit_headroom_ratio >= 0.3`, `recency <= 21` | "visits ~`<freq>`/wk, room for one more" | "one extra visit this week" | "frequency, target baseline+1" | `frequency` / low-mid |
| **churn_drift** | `churn_drift` | `overdue_ratio` in `1.2..2.6` (cooling) | "last visit `<recency>`d ago vs cadence `<cadence>`d — drifting" | "returns before the deadline" | "frequency win-back, stronger reward" | `frequency` / medium-high |
| **dormant_gap** | `dormant_gap` | `overdue_ratio > 2.6` / very high recency (dormant) | "absent `<recency>`d, near-lapsed" | "a single return visit" | "low-friction frequency, target 1, strong reward" | `frequency` / high |
| **basket_depth** | `basket_depth` | `basket_index >= 1.2` and `category_breadth >= 3` | "large baskets ~`<basket>`₽ across many categories" | "adds a complementary category/combo" | "basket/collection pairing" | `basket`/`collection` / XP |
| **streak_continuity** | `streak_continuity` | last plan `completed` / rigid routine | "completed last challenge / consistent weeks" | "keeps the routine alive" | "sustain visit_frequency, XP only" | — XP/league streak, not a challenge (support only) |
| **reward_posture** | `reward_posture` | any (meta, ties posture→reward) | "promo_sensitivity `<x>` → `<posture>`" | "reward mix matches posture" | "xp_level always; points_level per posture/budget" | — (guides reward, not a challenge) |
| **staple_avoid** | `<category>_staple_avoid` | a category with very high `share` (every-trip) | "`<cat>` is an every-trip staple (share `<x>`)" | "do NOT reward the staple (deadweight)" | "avoid category=`<cat>`; use frequency/other" | negative guard |

Anti-hallucination rules (enforced by validator + prompt):
- `name` must match the kind convention (snake_case; category-scoped kinds embed the category).
- `evidence_metric` must resolve to a real number from Part 1 (not free text).
- At least one insight must be an **action** kind (lapsed_category / visit_headroom /
  momentum_ride / churn_drift / dormant_gap / basket_depth); `reward_posture`, `streak_continuity`
  as continuity-only, and `staple_avoid` are supporting, not enough on their own.
- Every challenge's `insight_ref` must equal one instantiated insight `name`; the general
  strategy's `insight_refs` must cover **all** instantiated names.

---

## Part 5. Few-shot examples (embed in the prompt)

Each example shows the full staged output. Numbers are consistent with the thresholds above.
`thinking` is shortened for the doc; in production it is the real reasoning trace.

### 5.1. Steady Everyday Regular with Room for One More Trip and a Lapsed Dairy Run (value-selective)

Input snapshot (compact):
```
segment=regular_mid, frequency_per_week=1.3, recency_days=6, cadence_days=6.5,
churn_risk=none, avg_basket=560, promo_sensitivity=0.48, baseline_visits=1
derived: visit_momentum=1.02, overdue_ratio=0.92, cadence_regularity=0.71,
         visit_headroom_ratio=0.57, basket_index=0.93, category_breadth=2,
         top_category_overdue_ratio=2.67
category_timeseries: dairy{cadence=6, days_overdue=10, share=0.22, visits=12},
                     bakery{cadence=3, days_overdue=0, share=0.41, visits=22}  # staple
```
Output:
```
thinking: "On-cadence regular (overdue_ratio 0.92 -> steady) with room for one more trip
           (visit_headroom_ratio 0.57). Dairy is 10d overdue on a 6d cycle (top_cat_overdue 2.67)
           and it's a real 22% category, not the staple -> a timely incremental trip. Bakery is
           every-trip (41%), rewarding it would be deadweight. promo_sensitivity 0.48 = selective,
           so XP always + points only up to medium where it hits a real need."
classification:
  keywords: [steady, has_headroom, dairy_lapsed, day_to_day]   # lifecycle first
  label: "Steady Everyday Regular with Room for One More Trip and a Lapsed Dairy Run"
  description: "An on-cadence weekly regular who still has one extra trip in them and has let
                their usual dairy run lapse a full cycle."
  evidence:
    - "steady: cadence_regularity=0.71, overdue_ratio=0.92"
    - "has_headroom: visit_headroom_ratio=0.57, recency_days=6"
    - "dairy_lapsed: top_category_overdue_ratio=2.67 (dairy.days_overdue=10 on 6d cycle)"
    - "day_to_day: bakery.share=0.41 (every-trip staple)"
  posture: value_selective
  is_ambiguous: false
goal:
  target: visit_frequency   proxy: lapsed_category_rebuy   direction: recover
  rationale: "dairy is a full cycle overdue (top_category_overdue_ratio=2.67) — win that
              incremental trip back; the re-buy IS the extra visit, so it serves visit_frequency"
insights:
  - name: dairy_lapsed        behaviour: "buys dairy every ~6d but none for 16d"
    dod: "re-buys dairy within a week"  strategy_hint: "replenishment on dairy, target 1"
    evidence_metric: "dairy.days_overdue=10"
  - name: visit_headroom      behaviour: "visits ~1.3/wk with room for one more"
    dod: "one extra visit this week"    strategy_hint: "frequency, target baseline+1"
    evidence_metric: "visit_headroom_ratio=0.57"
  - name: bakery_staple_avoid behaviour: "bakery is an every-trip staple (share 0.41)"
    dod: "do not reward the staple"     strategy_hint: "avoid category=bakery"
    evidence_metric: "bakery.share=0.41"
challenges:
  - role: hero  insight_ref: dairy_lapsed   challenge_type: replenishment  category: dairy
    target: 1   reward: {xp_level: medium, points_level: medium}  deadline_days: 7
    rationale: "dairy 10d overdue on a 6d cycle — a timely re-buy trip, points justified on a real need"
  - role: side  insight_ref: visit_headroom challenge_type: frequency      category: null
    target: 2   reward: {xp_level: low, points_level: none}       deadline_days: 7
    rationale: "one extra trip above baseline 1, XP only"
general_strategy:
  insight_refs: [dairy_lapsed, visit_headroom, bakery_staple_avoid]
  rationale: "Recover visit_frequency via the lapsed_category_rebuy proxy (dairy) with a selective
              mid points reward, nudge one extra visit with XP only, and deliberately avoid paying
              for the bakery staple (deadweight)."
  next_week_hint: "if dairy completed, drop the proxy and switch hero to plain visit_headroom (XP-led)."
```

### 5.2. Dormant but Formerly-Active Big-Basket Everyday Shopper (deal-driven win-back)

Input snapshot:
```
segment=dormant, frequency_per_week=0.4, recency_days=30, cadence_days=7,
churn_risk=high, avg_basket=980, promo_sensitivity=0.68, baseline_visits=1
derived: visit_momentum=0.35, overdue_ratio=4.29, cadence_regularity=0.22,
         visit_headroom_ratio=0.0 (inactive: recency 30>21), basket_index=1.63,
         category_breadth=3, top_category_overdue_ratio=1.0
category_timeseries: (was a broad weekly shopper; no single category cleanly overdue now)
```
Output:
```
thinking: "30d since last visit on a 7d cadence = overdue_ratio 4.29 -> dormant, and visit_momentum
           0.35 shows they used to come far more (formerly_active). Big 980₽ baskets (basket_index
           1.63) across categories when they DO come. No single lapsed category to anchor, so this
           is a pure win-back: get ONE return trip. promo_sensitivity 0.68 = deal-driven -> XP high
           + points high to pull them back; a token reward would be ignored."
classification:
  keywords: [dormant, formerly_active, large_basket, day_to_day]
  label: "Dormant but Formerly-Active Big-Basket Everyday Shopper"
  description: "A once-weekly, big-basket everyday shopper who has gone quiet a full month and
                needs one strong reason to come back."
  evidence:
    - "dormant: overdue_ratio=4.29 (recency_days=30 vs cadence_days=7)"
    - "formerly_active: visit_momentum=0.35"
    - "large_basket: basket_index=1.63 (avg_basket=980)"
    - "day_to_day: was a broad every-week staple shopper"
  posture: deal_driven
  is_ambiguous: false
goal:
  target: visit_frequency   proxy: none   direction: recover
  rationale: "dormant (overdue_ratio=4.29) — the only job is one return trip; nothing to deepen yet"
insights:
  - name: dormant_gap    behaviour: "absent 30d vs 7d cadence, near-lapsed"
    dod: "a single return visit within the deadline"
    strategy_hint: "low-friction frequency target 1, strong reward"  evidence_metric: "recency_days=30"
  - name: reward_posture behaviour: "promo_sensitivity 0.68 -> deal_driven"
    dod: "reward strong enough to move a deal-seeker"
    strategy_hint: "xp high + points high"  evidence_metric: "promo_sensitivity=0.68"
challenges:
  - role: hero  insight_ref: dormant_gap  challenge_type: frequency  category: null
    target: 1  reward: {xp_level: high, points_level: high}  deadline_days: 10
    rationale: "one return trip after 30d away, high points to win back a deal-seeker, XP on top"
general_strategy:
  insight_refs: [dormant_gap, reward_posture]
  rationale: "Recover visit_frequency with a single low-friction return visit, priced high because
              30d absent + deal-driven justifies the spend; anything smaller gets ignored."
  next_week_hint: "if they return, lifecycle shifts dormant -> cooling; once stable, switch target
                   to basket_value (their baskets are already big) and drop points to medium."
```

### 5.3. At-Ceiling Steady Loyalist with Big Broad Baskets (promo-immune, grow the basket)

Input snapshot:
```
segment=heavy, frequency_per_week=2.8, recency_days=2, cadence_days=2.5,
churn_risk=none, avg_basket=1100, promo_sensitivity=0.2, baseline_visits=3
derived: visit_momentum=1.05, overdue_ratio=0.80, cadence_regularity=0.85,
         visit_headroom_ratio=0.07 (near ceiling), basket_index=1.83,
         category_breadth=4, top_category_overdue_ratio=1.0
previous_plans: [{challenge_type: collection, status: completed, used: true}]
```
Output:
```
thinking: "Frequent (2.8/wk), on-cadence, zero churn, but visit_headroom_ratio 0.07 = at their own
           ceiling — adding trips is pointless. Large 1100₽ baskets across 4 categories
           (basket_index 1.83). With no frequency headroom, the only budget lever is basket_value,
           hit via the add_category proxy (a new pairing). promo_sensitivity 0.2 = immune -> XP
           only; cash would be pure deadweight. No streak challenge — sustain is XP/league, not a
           challenge type."
classification:
  keywords: [steady, at_ceiling, large_basket, broad]
  label: "At-Ceiling Steady Loyalist with Big Broad Baskets"
  description: "A clockwork champion already at their visit ceiling whose only headroom is a
                slightly bigger, broader basket."
  evidence:
    - "steady: cadence_regularity=0.85, overdue_ratio=0.80"
    - "at_ceiling: visit_headroom_ratio=0.07"
    - "large_basket: basket_index=1.83 (avg_basket=1100)"
    - "broad: category_breadth=4"
  posture: promo_immune
  is_ambiguous: false
goal:
  target: basket_value   proxy: add_category   direction: increase
  rationale: "at ceiling on trips (visit_headroom_ratio=0.07) but large broad baskets
              (basket_index=1.83, category_breadth=4) — grow basket_value by adding a category,
              not the trip count"
insights:
  - name: basket_depth        behaviour: "large baskets ~1100₽ across 4 categories"
    dod: "adds one complementary category/combo"  strategy_hint: "collection pairing (add_category)"
    evidence_metric: "basket_index=1.83"
  - name: streak_continuity   behaviour: "completed last challenge, rigid weekly routine"
    dod: "keeps the routine alive this week"  strategy_hint: "sustain visit_frequency, XP/league only"
    evidence_metric: "previous_plans.status=completed"
challenges:
  - role: hero  insight_ref: basket_depth  challenge_type: collection  category: null
    target: 2  reward: {xp_level: high, points_level: none}  deadline_days: 7
    rationale: "deepen the 1100₽ basket with a new pairing, XP only — cash is deadweight here"
general_strategy:
  insight_refs: [basket_depth, streak_continuity]
  rationale: "A promo-immune champion: no points (deadweight). Grow basket_value via add_category
              with XP, and let their routine sustain itself through XP/league streak — which is a
              mechanic, not a challenge, so it carries no challenge card."
  next_week_hint: "rotate collection categories to avoid fatigue; keep points_level=none."
```

### 5.4. Cooling Regular Drifting Off Their Weekly Rhythm (value-selective)

Input snapshot:
```
segment=regular_mid, frequency_per_week=0.8, recency_days=13, cadence_days=7,
churn_risk=elevated, avg_basket=600, promo_sensitivity=0.5, baseline_visits=1
derived: visit_momentum=0.62, overdue_ratio=1.86, cadence_regularity=0.5,
         visit_headroom_ratio=0.73, basket_index=1.0, category_breadth=2,
         top_category_overdue_ratio=1.4
category_timeseries: (no single category a full cycle overdue)
```
Output:
```
thinking: "13d since last visit on a 7d cadence = overdue_ratio 1.86 -> cooling but still reachable,
           and visit_momentum 0.62 shows they were coming more before (formerly_active). Plenty of
           headroom (0.73). No category cleanly overdue, so no proxy — recover the rhythm head-on
           with a frequency task. promo_sensitivity 0.5 = selective -> XP + points up to medium as
           a timely win-back nudge."
classification:
  keywords: [cooling, formerly_active, has_headroom]
  label: "Cooling Regular Drifting Off Their Weekly Rhythm"
  description: "A weekly regular slipping off cadence but still active and reachable, with room to
                get back to their old pace."
  evidence:
    - "cooling: overdue_ratio=1.86 (recency_days=13 vs cadence_days=7)"
    - "formerly_active: visit_momentum=0.62"
    - "has_headroom: visit_headroom_ratio=0.73, recency_days=13"
  posture: value_selective
  is_ambiguous: false
goal:
  target: visit_frequency   proxy: none   direction: recover
  rationale: "cooling (overdue_ratio=1.86) and still reachable — recover the weekly rhythm before
              any decline hardens; no category overdue, so proxy=none"
insights:
  - name: churn_drift     behaviour: "last visit 13d ago vs 7d cadence — drifting off"
    dod: "returns before the deadline"  strategy_hint: "frequency win-back, medium reward"
    evidence_metric: "overdue_ratio=1.86"
  - name: visit_headroom  behaviour: "was ~1.3/wk, now 0.8/wk with room to recover"
    dod: "back to two trips this week"  strategy_hint: "frequency, target baseline+1"
    evidence_metric: "visit_headroom_ratio=0.73"
challenges:
  - role: hero  insight_ref: churn_drift  challenge_type: frequency  category: null
    target: 2  reward: {xp_level: medium, points_level: medium}  deadline_days: 7
    rationale: "two trips this week to reset the weekly rhythm, points to nudge a slipping regular"
general_strategy:
  insight_refs: [churn_drift, visit_headroom]
  rationale: "Recover visit_frequency head-on (proxy none) while there's still momentum: a timely
              frequency task with a medium points nudge, using their clear headroom."
  next_week_hint: "if they return, lifecycle shifts cooling -> steady; drop points_level to none and
                   sustain with XP."
```

---

## Part 6. How this plugs in (no code yet)

- **Insight builder** (`insight.py`): compute the seven derived signals (Part 1b) and add them to
  `PlannerFeatures`, so both the model and the fallback derive the same buyer keywords.
- **Prompt** (`planner_system.md`): embed Part 1b (derived signals), Part 2 (keyword palette +
  posture + the two-target/proxy goal rule + the two-currency reward rule), Part 3 (name-the-buyer
  + goal pick), Part 4 (insight kinds), and 2–3 few-shots from Part 5. The closed vocabularies +
  explicit metric->keyword map are what keep the model from randomising.
- **Validator** (`validator.py`): enforce the closed keyword palette (one lifecycle + 0..4
  modifiers, `label`/`description` drawn only from chosen keywords), the **two** `goal.target`
  values + `goal.proxy` enum with valid target/direction pairings, a hero mechanic that matches
  `target` via its `proxy`, the **5 canonical `ChallengeType`s (no `streak`)**, the two-currency
  reward **never-none** rule (`xp_level` always set; `points_level` `none` or within the economics
  budget), `insight_ref` integrity, the "at least one action insight" rule, and evidence resolving
  to a real number (Part 4).
- **Fallback** (`rules.py`): reuse Part 3's derivation to produce the buyer keywords, the `goal`
  (target + proxy + direction), the reward mix, 1–2 insights, and the hero challenge
  deterministically, so offline runs match the taxonomy.
- **Eval** (`verify-classification`): score the buyer keywords against the segment->plausible map
  (Part 3), plus goal-vs-keywords coherence, reward-vs-posture-and-budget, insight-grounding and
  reference integrity — see `planner-v2-classification-insights.md` §14.

**Schema change flagged (proposal, code not yet touched):** today `app/ml/schemas.py` still has
`ChallengeType` including `streak` and a single reward shape `reward_kind (promo/ladder/none)` +
`reward_level`. This taxonomy proposes: drop `streak` from `ChallengeType` (→ 5 canonical, per
E17), replace `engagement[]`/`posture` classification with the keyword `classification`
(`keywords`/`label`/`description`/`evidence`) + `posture`, replace the 4-target `goal.target` with
the 2-target + `goal.proxy` shape, and replace `reward_kind`/`reward_level` with
`reward.{xp_level, points_level}`. These land when the planner is integrated (E17 BE-038 / AI-013).

---

## Where to go next
- Plain-language rationale — `planner-v2-explained.md`.
- The v2 architecture and schema — `planner-v2-classification-insights.md` (RU; still on the old
  ranked-`engagement` + 4-target framing, not yet synced to this "name the buyer" + 2-target +
  proxy + two-currency-reward design — this file is the current source of truth for v2).
- Today's planner — `ml-rework-explained.md`.
