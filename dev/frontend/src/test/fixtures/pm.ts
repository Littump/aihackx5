import { heroChallenge } from "./challenges";
import type {
  Achievement,
  EvalRun,
  FraudCheck,
  PmUserResponse,
  SimulationRun,
  UserFeatures,
} from "./types";
import { getUserSummary } from "./users";

const FEATURES_BY_USER: Record<number, UserFeatures> = {
  1: {
    computed_at: "2026-09-02T06:00:00+03:00",
    window_weeks: 10,
    frequency_per_week: 2,
    recency_days: 3,
    avg_basket: 600,
    promo_sensitivity: 0.35,
    cadence_days: 3.5,
    category_affinity: { dairy: { share: 0.32, visits: 4, cadence_days: 4 } },
    realized_savings_30d: 1240,
    favourite_store_id: 101,
    cross_chain_share: 0.1,
  },
  2: {
    computed_at: "2026-09-02T06:00:00+03:00",
    window_weeks: 10,
    frequency_per_week: 3.2,
    recency_days: 1,
    avg_basket: 450,
    promo_sensitivity: 0.5,
    cadence_days: 2.2,
    category_affinity: { meat_fish: { share: 0.28, visits: 6, cadence_days: 5 } },
    realized_savings_30d: 860,
    favourite_store_id: 202,
    cross_chain_share: 0.2,
  },
  3: {
    computed_at: "2026-09-02T06:00:00+03:00",
    window_weeks: 10,
    frequency_per_week: 0.5,
    recency_days: 12,
    avg_basket: 300,
    promo_sensitivity: 0.1,
    cadence_days: 14,
    category_affinity: {},
    realized_savings_30d: 120,
    favourite_store_id: 101,
    cross_chain_share: 0,
  },
};

export function getFraudChecks(): FraudCheck[] {
  return [
    {
      id: 1,
      subject_type: "receipt",
      subject_id: 501,
      user_id: 2,
      score: 0.62,
      decision: "hold",
      signals: [
        { code: "frequency_spike", weight: 0.2, strong: false, detail: "4x частота за неделю" },
      ],
      created_at: "2026-09-01T14:00:00+03:00",
    },
  ];
}

export function getAchievements(): Achievement[] {
  return [
    { code: "first_receipt", title: "Первый чек", unlocked_at: "2026-07-01T10:00:00+03:00" },
    { code: "first_challenge", title: "Первый челлендж", unlocked_at: "2026-07-14T18:20:00+03:00" },
  ];
}

export function getPmUser(userId: number): PmUserResponse {
  return {
    user: getUserSummary(userId),
    features: FEATURES_BY_USER[userId] ?? FEATURES_BY_USER[1],
    recommended_mechanic: {
      mechanic: "challenge",
      reasons: ["Нет выполненных челленджей на этой неделе"],
    },
    hero_challenge: heroChallenge(userId),
    rewards_total_points: 620,
    rewards_total_xp: 890,
    expected_incremental_margin_month: 360,
    fraud_checks: getFraudChecks().filter((check) => check.user_id === userId),
    ledger: [
      {
        kind: "receipt",
        xp_delta: 10,
        points_delta: 0,
        ref_type: "receipt",
        ref_id: 501,
        created_at: "2026-09-01T14:00:00+03:00",
      },
    ],
  };
}

export function getSimulationRun(): SimulationRun {
  return {
    id: 1,
    created_at: "2026-08-28T09:00:00+03:00",
    params: { users: 5000, weeks: 8, treatment_share: 0.3 },
    results: {
      purchases_per_user_control: 4.1,
      purchases_per_user_treatment: 4.5,
      share_above_n_control: 0.21,
      share_above_n_treatment: 0.29,
      frequency_uplift: 0.07,
      incremental_revenue: 184000,
      incremental_margin: 27600,
      reward_cost: 9200,
      net_effect: 18400,
      referral_conversion: 0.18,
      fraud_precision: 0.83,
      fraud_recall: 0.71,
    },
  };
}

export function getEvalRun(): EvalRun {
  return {
    id: 1,
    created_at: "2026-08-28T09:00:00+03:00",
    profiles: 40,
    hit_rate: 0.78,
    invalid_rate: 0.02,
    fallback_rate: 0.15,
    economics_pass_rate: 0.92,
    details: [{ profile_id: 1, relevant: true }],
  };
}
