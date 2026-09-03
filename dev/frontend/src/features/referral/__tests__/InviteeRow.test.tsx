import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { InviteeRow } from "../components/InviteeRow";
import type { ReferralInvitee, ReferralStatus } from "../format";

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

describe("InviteeRow", () => {
  it.each(["pending", "first_purchase"] satisfies ReferralStatus[])(
    "статус «%s» показывает бейдж с прогрессом покупок",
    (status) => {
      render(
        <InviteeRow invitee={invitee({ status, purchases_done: 1, purchases_required: 2 })} />,
      );
      expect(screen.getByText("1 из 2 покупок")).toBeInTheDocument();
    },
  );

  it.each([
    ["qualified", "выполнил условия"],
    ["on_review", "на проверке"],
    ["rewarded", "награда получена"],
    ["blocked", "отклонён"],
  ] satisfies [ReferralStatus, string][])(
    "статус «%s» показывает бейдж с текстом статуса «%s», а не прогресс",
    (status, text) => {
      render(
        <InviteeRow invitee={invitee({ status, purchases_done: 2, purchases_required: 2 })} />,
      );
      expect(screen.getByText(text)).toBeInTheDocument();
      expect(screen.queryByText("2 из 2 покупок")).not.toBeInTheDocument();
    },
  );
});
