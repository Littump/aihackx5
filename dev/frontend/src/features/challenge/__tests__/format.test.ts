import { describe, expect, it } from "vitest";
import { formatChallengeHistoryStatus } from "../format";

describe("formatChallengeHistoryStatus", () => {
  it("completed → выполнено, тон success", () => {
    expect(formatChallengeHistoryStatus("completed")).toEqual({
      text: "выполнено",
      tone: "success",
    });
  });

  it("failed → не успели, тон inProgress", () => {
    expect(formatChallengeHistoryStatus("failed")).toEqual({
      text: "не успели",
      tone: "inProgress",
    });
  });

  it("expired → истекло, тон failed", () => {
    expect(formatChallengeHistoryStatus("expired")).toEqual({
      text: "истекло",
      tone: "failed",
    });
  });

  it("active (не должен встречаться в истории) → нейтральный тон", () => {
    expect(formatChallengeHistoryStatus("active")).toEqual({
      text: "активно",
      tone: "neutral",
    });
  });
});
