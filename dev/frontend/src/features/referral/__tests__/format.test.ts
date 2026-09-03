import { describe, expect, it } from "vitest";
import {
  formatInviteeBadge,
  limitText,
  purchasesProgressText,
  statusIconShape,
  statusText,
  statusToneClasses,
  type ReferralInvitee,
  type ReferralStatus,
} from "../format";

const ALL_STATUSES: ReferralStatus[] = [
  "pending",
  "first_purchase",
  "qualified",
  "on_review",
  "rewarded",
  "blocked",
];

function invitee(overrides: Partial<ReferralInvitee>): ReferralInvitee {
  return {
    label: "Сосед №1",
    referee_kind: "new",
    status: "pending",
    purchases_done: 1,
    purchases_required: 2,
    reward_points: 0,
    created_at: "2026-08-10T12:00:00+03:00",
    ...overrides,
  };
}

describe("statusText", () => {
  it.each([
    ["pending", "ожидает"],
    ["first_purchase", "первая покупка"],
    ["qualified", "выполнил условия"],
    ["on_review", "на проверке"],
    ["rewarded", "награда получена"],
    ["blocked", "отклонён"],
  ] satisfies [ReferralStatus, string][])("статус «%s» показывает текст «%s»", (status, text) => {
    expect(statusText(status)).toBe(text);
  });
});

describe("иконки и тон статусов", () => {
  it("каждый из 6 статусов контракта имеет собственную непустую иконку и тон", () => {
    for (const status of ALL_STATUSES) {
      expect(statusIconShape(status).length).toBeGreaterThan(0);
      expect(statusToneClasses(status)).not.toBe("");
    }
  });

  it("иконки всех 6 статусов уникальны", () => {
    const serialized = ALL_STATUSES.map((status) => JSON.stringify(statusIconShape(status)));
    expect(new Set(serialized).size).toBe(ALL_STATUSES.length);
  });
});

describe("formatInviteeBadge", () => {
  it("для pending и first_purchase показывает прогресс покупок", () => {
    expect(formatInviteeBadge(invitee({ status: "pending", purchases_done: 0 }))).toBe(
      "0 из 2 покупок",
    );
    expect(formatInviteeBadge(invitee({ status: "first_purchase", purchases_done: 1 }))).toBe(
      "1 из 2 покупок",
    );
  });

  it.each([
    ["qualified", "выполнил условия"],
    ["on_review", "на проверке"],
    ["rewarded", "награда получена"],
    ["blocked", "отклонён"],
  ] satisfies [ReferralStatus, string][])(
    "для статуса «%s» показывает текст статуса «%s», а не прогресс",
    (status, text) => {
      expect(formatInviteeBadge(invitee({ status, purchases_done: 2 }))).toBe(text);
    },
  );
});

describe("purchasesProgressText", () => {
  it("форматирует прогресс покупок", () => {
    expect(purchasesProgressText(1, 2)).toBe("1 из 2 покупок");
    expect(purchasesProgressText(0, 2)).toBe("0 из 2 покупок");
  });
});

describe("граница: first_purchase с покупками на пределе требуемых", () => {
  it("не ломает текст, когда purchases_done === purchases_required", () => {
    expect(
      formatInviteeBadge(
        invitee({ status: "first_purchase", purchases_done: 2, purchases_required: 2 }),
      ),
    ).toBe("2 из 2 покупок");
  });
});

describe("нейтральность on_review и blocked", () => {
  it.each(["on_review", "blocked"] satisfies ReferralStatus[])(
    "тон статуса «%s» не использует тревожную/акцентную палитру",
    (status) => {
      expect(statusToneClasses(status)).not.toMatch(/accent/);
    },
  );
});

describe("limitText", () => {
  it("форматирует лимит месяца", () => {
    expect(limitText(2, 5)).toBe("выплачено 2 из 5");
    expect(limitText(4, 5)).toBe("выплачено 4 из 5");
  });
});
