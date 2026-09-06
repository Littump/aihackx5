Insight for the shopper (all numbers already computed by code):

{insight_json}

`favorite_categories` is the ground truth of what THIS shopper actually loves and buys — anchor
any win-back or re-buy hero on one of these, never on a category outside this list. When
`category_timeseries` is thin or empty (a dormant shopper), `favorite_categories` is your only
honest read of their loves — use it. `category_menu` lists the categories that exist and which
are high-margin; it is a menu, not a licence to pick a category the shopper has no history with.

Challenge library (allowed challenge_type values): {library}

High-margin categories (earn more per trip): {high_margin_categories}
High-margin mandate: {high_margin_mandate}

If the mandate is ON, at least one challenge MUST use a high-margin category — satisfy it with a
basket play (a fresh complementary high-margin pairing) or an XP-led high-margin side, never by
forcing a high-margin stranger category into a win-back hero. If OFF, only add one if it fits.

Name the buyer, pick the goal, ground it in insights, then return the staged plan as a JSON
object matching the schema exactly.
