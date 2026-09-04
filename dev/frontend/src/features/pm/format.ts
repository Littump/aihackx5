import type { FraudDecision } from "./api";

export const FRAUD_HOLD_THRESHOLD = 0.5; // зеркалит game_rules.FRAUD_HOLD_THRESHOLD
export const FRAUD_BLOCK_THRESHOLD = 0.8; // зеркалит game_rules.FRAUD_BLOCK_THRESHOLD

export function formatPercent(rate: number): string {
  return `${Math.round(rate * 100)}%`;
}

export function formatDays(days: number): string {
  return `${days.toFixed(1)} дн.`;
}

export function formatDateTime(iso: string): string {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Europe/Moscow",
  }).format(new Date(iso));
}

const DECISION_LABELS: Record<FraudDecision, string> = {
  approve: "Одобрено",
  hold: "Отложено",
  block: "Заблокировано",
};

export function decisionLabel(decision: FraudDecision): string {
  return DECISION_LABELS[decision];
}

const DECISION_BADGE_CLASSES: Record<FraudDecision, string> = {
  approve: "bg-brand-50 text-brand-700",
  hold: "bg-accent-50 text-accent-700",
  block: "bg-accent-600 text-white",
};

export function decisionBadgeClass(decision: FraudDecision): string {
  return DECISION_BADGE_CLASSES[decision];
}
