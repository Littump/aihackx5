import type { ReferralResponse } from "./api";

export type ReferralInvitee = ReferralResponse["invitees"][number];
export type ReferralStatus = ReferralInvitee["status"];

export type ReferralStatusIconShape =
  { tag: "path"; d: string } | { tag: "circle"; cx: number; cy: number; r: number };

type ReferralStatusInfo = {
  text: string;
  toneClasses: string;
  icon: ReferralStatusIconShape[];
};

const REFERRAL_STATUS_INFO: Record<ReferralStatus, ReferralStatusInfo> = {
  pending: {
    text: "ожидает",
    toneClasses: "bg-canvas text-ink-700",
    icon: [
      { tag: "circle", cx: 12, cy: 12, r: 8 },
      { tag: "path", d: "M12 8v4l3 2" },
    ],
  },
  first_purchase: {
    text: "первая покупка",
    toneClasses: "bg-accent-50 text-accent-700",
    icon: [{ tag: "path", d: "M6 6h13l-2 7H8zM8 13l-2-7H3" }],
  },
  qualified: {
    text: "выполнил условия",
    toneClasses: "bg-brand-50 text-brand-700",
    icon: [{ tag: "path", d: "m4 13 5 5L20 7" }],
  },
  on_review: {
    text: "на проверке",
    toneClasses: "bg-canvas text-ink-700",
    icon: [
      { tag: "circle", cx: 11, cy: 11, r: 6 },
      { tag: "path", d: "m16 16 4 4" },
    ],
  },
  rewarded: {
    text: "награда получена",
    toneClasses: "bg-brand-50 text-brand-700",
    icon: [{ tag: "path", d: "M3 8h18v4H3zM20 12v7a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-7M12 8v12" }],
  },
  blocked: {
    text: "отклонён",
    toneClasses: "bg-canvas text-ink-900",
    icon: [{ tag: "path", d: "M6 6l12 12M18 6 6 18" }],
  },
};

export function statusText(status: ReferralStatus): string {
  return REFERRAL_STATUS_INFO[status].text;
}

export function statusToneClasses(status: ReferralStatus): string {
  return REFERRAL_STATUS_INFO[status].toneClasses;
}

export function statusIconShape(status: ReferralStatus): ReferralStatusIconShape[] {
  return REFERRAL_STATUS_INFO[status].icon;
}

const PROGRESS_STATUSES: ReadonlySet<ReferralStatus> = new Set(["pending", "first_purchase"]);

export function purchasesProgressText(done: number, required: number): string {
  return `${done} из ${required} покупок`;
}

export function formatInviteeBadge(invitee: ReferralInvitee): string {
  if (PROGRESS_STATUSES.has(invitee.status)) {
    return purchasesProgressText(invitee.purchases_done, invitee.purchases_required);
  }
  return statusText(invitee.status);
}

export function limitText(paidThisMonth: number, paidLimitMonth: number): string {
  return `выплачено ${paidThisMonth} из ${paidLimitMonth}`;
}
