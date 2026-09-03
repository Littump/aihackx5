import type { ReferralResponse } from "./api";

export type ReferralInvitee = ReferralResponse["invitees"][number];
export type ReferralStatus = ReferralInvitee["status"];

const STATUS_LABELS: Record<ReferralStatus, string> = {
  pending: "ожидает",
  first_purchase: "ожидает",
  qualified: "выполнен",
  rewarded: "выполнен",
  on_review: "на проверке",
  blocked: "на проверке",
};

const STATUS_BADGE_CLASSES: Record<ReferralStatus, string> = {
  pending: "bg-bg text-text-secondary border border-border",
  first_purchase: "bg-bg text-text-secondary border border-border",
  qualified: "bg-legacy-brand-100 text-legacy-brand-600",
  rewarded: "bg-legacy-brand-100 text-legacy-brand-600",
  on_review: "bg-bg text-text-secondary border border-border",
  blocked: "bg-bg text-text-secondary border border-border",
};

export function statusLabel(status: ReferralStatus): string {
  return STATUS_LABELS[status];
}

export function statusBadgeClass(status: ReferralStatus): string {
  return STATUS_BADGE_CLASSES[status];
}

export function purchasesProgressText(done: number, required: number): string {
  return `${done} из ${required} покупок`;
}

export function limitText(paidThisMonth: number, paidLimitMonth: number): string {
  return `${paidThisMonth} из ${paidLimitMonth} в этом месяце`;
}
