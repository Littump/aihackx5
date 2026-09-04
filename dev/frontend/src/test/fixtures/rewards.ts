import type { RewardsResponse } from "./types";
import { DOMOVOY_BY_USER, POINTS_BALANCE_BY_USER } from "./users";

const RULES: RewardsResponse["rules"] = [
  {
    code: "receipt",
    title: "Чек засчитан: покупка в Пятёрочке или Перекрёстке",
    xp: 10,
    points_min: 0,
    points_max: 0,
  },
  { code: "challenge", title: "Цель недели выполнена", xp: 50, points_min: 30, points_max: 150 },
  {
    code: "referral",
    title: "Приглашённый сосед дошёл до второй покупки",
    xp: 100,
    points_min: 150,
    points_max: 150,
  },
];

const HISTORY_BY_USER: Record<number, RewardsResponse["history"]> = {
  1: [
    {
      id: 12,
      kind: "challenge",
      title: "Цель недели выполнена",
      detail: "Молочный ритм",
      xp_delta: 50,
      points_delta: 30,
      created_at: "2026-09-03T10:00:00+03:00",
    },
    {
      id: 11,
      kind: "receipt_xp",
      title: "Покупка засчитана",
      detail: "Чек на 640 ₽",
      xp_delta: 10,
      points_delta: 0,
      created_at: "2026-09-02T18:20:00+03:00",
    },
  ],
  2: [
    {
      id: 8,
      kind: "referral",
      title: "Приглашённый сосед",
      detail: null,
      xp_delta: 100,
      points_delta: 150,
      created_at: "2026-08-30T12:00:00+03:00",
    },
  ],
  3: [],
};

export function getRewards(userId: number): RewardsResponse {
  const domovoy = DOMOVOY_BY_USER[userId] ?? DOMOVOY_BY_USER[1];
  const balance = POINTS_BALANCE_BY_USER[userId] ?? POINTS_BALANCE_BY_USER[1];
  return {
    points_balance: balance,
    points_from_rewards: balance,
    points_from_receipts: 0,
    xp: domovoy.xp,
    level: domovoy.level,
    xp_to_next_level: domovoy.xp_to_next_level,
    rules: RULES,
    history: HISTORY_BY_USER[userId] ?? [],
  };
}
