import type { Challenge, ChallengeDetail } from "./types";

const WEEK_START = "2026-08-31T00:00:00+03:00";
const WEEK_END = "2026-09-06T23:59:59+03:00";

export function heroChallenge(userId: number): ChallengeDetail | null {
  if (userId === 3) return null;
  return {
    id: 1000 + userId,
    type: "frequency",
    category: null,
    status: "active",
    is_hero: true,
    baseline: 2,
    target: 3,
    progress: 2,
    period_start: WEEK_START,
    period_end: WEEK_END,
    reward_xp: 50,
    reward_points: 30,
    title: "3 покупки за неделю",
    body: "Обычно у вас 2 покупки в неделю. Сделайте 3 до воскресенья.",
    explanation: "Обычно 2 покупки в неделю (baseline 2), цель — 3 до конца недели.",
    rationale_features: { frequency_per_week: 2, recency_days: 3 },
    economics: {
      avg_basket: 600,
      expected_incremental_purchases: 1,
      expected_incremental_margin: 90,
      max_reward_rub: 36,
      contribution_margin: 0.15,
      reward_share_max: 0.4,
    },
    copy_source: "template",
  };
}

export function sideChallenges(userId: number): ChallengeDetail[] {
  if (userId === 3) return [];
  return [
    {
      id: 2000 + userId,
      type: "category",
      category: "dairy",
      status: "active",
      is_hero: false,
      baseline: 1,
      target: 2,
      progress: 1,
      period_start: WEEK_START,
      period_end: WEEK_END,
      reward_xp: 50,
      reward_points: 30,
      title: "2 покупки молочки за неделю",
      body: "Молочка у вас в топ-категориях — берите чаще.",
      explanation: "Доля молочки в корзине — 0.32, это выше порога 0.10.",
      rationale_features: { share: 0.32, visits: 4 },
      economics: {
        avg_basket: 600,
        expected_incremental_purchases: 1,
        expected_incremental_margin: 90,
        max_reward_rub: 36,
        contribution_margin: 0.15,
        reward_share_max: 0.4,
      },
      copy_source: "llm",
    },
  ];
}

const HISTORY_BY_USER: Record<number, Challenge[]> = {
  1: [
    {
      id: 900,
      type: "frequency",
      category: null,
      status: "completed",
      is_hero: true,
      baseline: 2,
      target: 3,
      progress: 3,
      period_start: "2026-08-24T00:00:00+03:00",
      period_end: "2026-08-30T23:59:59+03:00",
      reward_xp: 50,
      reward_points: 30,
      title: "3 покупки за неделю",
      body: "Обычно у вас 2 покупки в неделю. Сделайте 3 до воскресенья.",
    },
  ],
  2: [],
  3: [],
};

export function getChallengeList(userId: number) {
  return {
    hero: heroChallenge(userId),
    side: sideChallenges(userId),
    history: HISTORY_BY_USER[userId] ?? [],
  };
}

export function getChallengeDetail(userId: number, challengeId: number): ChallengeDetail {
  const candidates = [heroChallenge(userId), ...sideChallenges(userId)].filter(
    (challenge): challenge is ChallengeDetail => challenge !== null,
  );
  const fallback = heroChallenge(1);
  return (
    candidates.find((challenge) => challenge.id === challengeId) ??
    candidates[0] ??
    (fallback as ChallengeDetail)
  );
}
