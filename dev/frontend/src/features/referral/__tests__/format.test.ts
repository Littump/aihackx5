import { describe, expect, it } from "vitest";
import { limitText, purchasesProgressText, statusLabel, type ReferralStatus } from "../format";

describe("statusLabel", () => {
  it.each([
    ["pending", "ожидает"],
    ["first_purchase", "ожидает"],
    ["qualified", "выполнен"],
    ["rewarded", "выполнен"],
    ["on_review", "на проверке"],
    ["blocked", "на проверке"],
  ] satisfies [ReferralStatus, string][])(
    "статус «%s» показывает нейтральный текст «%s»",
    (status, expected) => {
      expect(statusLabel(status)).toBe(expected);
    },
  );

  it("on_review и blocked никогда не показывают панические формулировки", () => {
    expect(statusLabel("on_review")).not.toMatch(/заблокирован|отклонён|блок/i);
    expect(statusLabel("blocked")).not.toMatch(/заблокирован|отклонён|блок/i);
  });
});

describe("purchasesProgressText", () => {
  it("форматирует прогресс покупок", () => {
    expect(purchasesProgressText(1, 2)).toBe("1 из 2 покупок");
    expect(purchasesProgressText(0, 2)).toBe("0 из 2 покупок");
  });
});

describe("limitText", () => {
  it("форматирует лимит месяца", () => {
    expect(limitText(2, 5)).toBe("2 из 5 в этом месяце");
    expect(limitText(4, 5)).toBe("4 из 5 в этом месяце");
  });
});
