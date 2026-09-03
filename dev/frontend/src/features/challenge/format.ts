import type { StatusChipStatus } from "@/shared/ui/StatusChip";
import type { ChallengeDetail, ChallengeHistoryItem } from "./api";

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
  return `+${rewardXp} XP и ${rewardPoints} баллов`;
}

export function formatCompactReward(rewardXp: number, rewardPoints: number): string {
  return `+${rewardXp} XP · ${rewardPoints} баллов`;
}

type ChallengeHistoryStatus = ChallengeHistoryItem["status"];

type ChallengeHistoryStatusInfo = {
  text: string;
  tone: StatusChipStatus;
};

const HISTORY_STATUS_INFO: Record<ChallengeHistoryStatus, ChallengeHistoryStatusInfo> = {
  completed: { text: "выполнено", tone: "success" },
  failed: { text: "не успели", tone: "inProgress" },
  expired: { text: "истекло", tone: "failed" },
  active: { text: "активно", tone: "neutral" },
};

export function formatChallengeHistoryStatus(
  status: ChallengeHistoryStatus,
): ChallengeHistoryStatusInfo {
  return HISTORY_STATUS_INFO[status];
}
