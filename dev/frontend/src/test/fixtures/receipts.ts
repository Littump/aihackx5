import { DOMOVOY_BY_USER } from "./users";
import type { Receipt, ReceiptProcessingResult } from "./types";

export function getReceipts(): Receipt[] {
  return [
    {
      id: 5001,
      store_id: 101,
      store_name: "Пятёрочка на Ленина",
      purchased_at: "2026-09-02T18:32:00+03:00",
      regular_total: 780,
      paid_total: 640,
      discount_total: 140,
      points_earned: 32,
      points_spent: 0,
      counted: true,
      is_returned: false,
      items: [
        {
          product_name: "Молоко 3.2%",
          category: "dairy",
          qty: 2,
          regular_price: 89,
          paid_price: 79,
          is_promo: true,
        },
      ],
    },
  ];
}

export function buildReceiptProcessingResult(userId: number): ReceiptProcessingResult {
  return {
    receipt: getReceipts()[0],
    counted: true,
    counted_reason: null,
    xp_delta: 10,
    domovoy: DOMOVOY_BY_USER[userId] ?? DOMOVOY_BY_USER[1],
    savings_delta: 172,
    challenges: [
      {
        challenge_id: 1000 + userId,
        progress_before: 2,
        progress_after: 3,
        target: 3,
        completed: true,
        reward_points: 30,
        reward_xp: 50,
      },
    ],
    league_rank_before: 6,
    league_rank_after: 5,
    referral_status: null,
    fraud: { score: 0.1, decision: "approve", signals: [] },
    achievements_unlocked: [],
  };
}
