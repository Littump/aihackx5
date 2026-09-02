import type { ReferralResponse } from "./types";

export function getReferral(userId: number): ReferralResponse {
  return {
    code: `DOM-${userId}F2B`,
    link: `https://x5club.ru/i/DOM-${userId}F2B`,
    rules: ["Пригласите соседа по коду", "Награда после второй покупки приглашённого"],
    referrer_reward_points: 150,
    referee_reward_points_new: 200,
    referee_reward_points_dormant: 150,
    invitees: [
      {
        label: "Сосед №1",
        referee_kind: "new",
        status: "rewarded",
        purchases_done: 2,
        purchases_required: 2,
        reward_points: 200,
        created_at: "2026-08-10T12:00:00+03:00",
      },
      {
        label: "Сосед №2",
        referee_kind: "dormant",
        status: "first_purchase",
        purchases_done: 1,
        purchases_required: 2,
        reward_points: 150,
        created_at: "2026-08-25T09:30:00+03:00",
      },
    ],
    paid_this_month: 1,
    paid_limit_month: 5,
  };
}
