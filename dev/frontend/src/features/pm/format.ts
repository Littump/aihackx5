import type { FraudDecision, PmUserResponse } from "./api";

export function formatPercent(rate: number): string {
  return `${Math.round(rate * 100)}%`;
}

export function formatDateTime(iso: string): string {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
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
  approve: "bg-brand-100 text-brand-600",
  hold: "bg-accent-100 text-accent-600",
  block: "bg-accent-600 text-white",
};

export function decisionBadgeClass(decision: FraudDecision): string {
  return DECISION_BADGE_CLASSES[decision];
}

type Mechanic = PmUserResponse["recommended_mechanic"]["mechanic"];

const MECHANIC_LABELS: Record<Mechanic, string> = {
  challenge: "Челлендж",
  league: "Лига",
  referral: "Рефералы",
};

export function mechanicLabel(mechanic: Mechanic): string {
  return MECHANIC_LABELS[mechanic];
}
