import { heroChallenge } from "./challenges";
import type { HomeResponse } from "./types";
import { DOMOVOY_BY_USER, POINTS_BALANCE_BY_USER, SAVINGS_BY_USER, getUserSummary } from "./users";

export function getHome(userId: number): HomeResponse {
  return {
    user: getUserSummary(userId),
    domovoy: DOMOVOY_BY_USER[userId] ?? DOMOVOY_BY_USER[1],
    savings: SAVINGS_BY_USER[userId] ?? SAVINGS_BY_USER[1],
    points_balance: POINTS_BALANCE_BY_USER[userId] ?? POINTS_BALANCE_BY_USER[1],
    insight: "На прошлой неделе вы сэкономили больше обычного на молочке.",
    hero_challenge: heroChallenge(userId),
    league: userId === 3 ? null : { division: 2, rank: 5, size: 28, zone: "safe" },
    referral: { code: `DOM-${userId}F2B`, invited_count: 3, rewarded_count: 1 },
    recommended_mechanic: {
      mechanic: "challenge",
      reason: "Ещё нет выполненных челленджей на этой неделе",
    },
  };
}
