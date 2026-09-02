import type { ChallengeDetail } from "./api";

type ChallengeType = ChallengeDetail["type"];

const CHALLENGE_TYPE_LABELS: Record<ChallengeType, string> = {
  frequency: "Частота покупок",
  category: "Категория товаров",
};

export function formatChallengeType(type: ChallengeType): string {
  return CHALLENGE_TYPE_LABELS[type];
}

export function formatDeadline(periodEnd: string): string {
  return new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "long" }).format(
    new Date(periodEnd),
  );
}

export function formatReward(rewardXp: number, rewardPoints: number): string {
  return `+${rewardXp} XP + ${rewardPoints} баллов`;
}
