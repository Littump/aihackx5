import { describe, expect, it } from "vitest";
import {
  formatPercent,
  formatRankChangeMessage,
  formatWeekRange,
  isDemotionBoundary,
  isPromotionBoundary,
  zoneForRank,
  zoneLabel,
  zoneRowClass,
} from "../format";

const PROMOTION_CUTOFF = 7;
const DEMOTION_CUTOFF = 20;

describe("zoneForRank", () => {
  it.each([
    [6, "promotion"],
    [7, "promotion"],
    [8, "safe"],
    [19, "safe"],
    [20, "demotion"],
    [24, "demotion"],
  ])("для места %i возвращает зону «%s»", (rank, zone) => {
    expect(zoneForRank(rank, PROMOTION_CUTOFF, DEMOTION_CUTOFF)).toBe(zone);
  });
});

describe("zoneLabel", () => {
  it.each([
    ["promotion", "Повышение"],
    ["safe", "Безопасная"],
    ["demotion", "Понижение"],
  ] as const)("для зоны «%s» возвращает «%s»", (zone, label) => {
    expect(zoneLabel(zone)).toBe(label);
  });
});

describe("zoneRowClass", () => {
  it("зона demotion получает полупрозрачный фон", () => {
    expect(zoneRowClass("demotion")).toBe("bg-accent-50/50");
  });

  it.each(["promotion", "safe"] as const)("зона «%s» не получает специального фона", (zone) => {
    expect(zoneRowClass(zone)).toBe("");
  });
});

describe("isPromotionBoundary / isDemotionBoundary", () => {
  it("разделитель повышения стоит ровно на promotion_cutoff", () => {
    for (let rank = 1; rank <= 24; rank += 1) {
      expect(isPromotionBoundary(rank, PROMOTION_CUTOFF)).toBe(rank === PROMOTION_CUTOFF);
    }
  });

  it("разделитель понижения стоит ровно на demotion_cutoff", () => {
    for (let rank = 1; rank <= 24; rank += 1) {
      expect(isDemotionBoundary(rank, DEMOTION_CUTOFF)).toBe(rank === DEMOTION_CUTOFF);
    }
  });
});

describe("formatWeekRange", () => {
  it("форматирует неделю на стыке месяцев", () => {
    expect(formatWeekRange("2026-08-31", "2026-09-06")).toBe("31 августа – 6 сентября");
  });

  it("форматирует неделю внутри одного месяца", () => {
    expect(formatWeekRange("2026-09-01", "2026-09-07")).toBe("1 сентября – 7 сентября");
  });
});

describe("formatPercent", () => {
  it.each([
    [0.12, "12%"],
    [0.5, "50%"],
    [0.005, "1%"],
    [0, "0%"],
  ])("округляет %f до «%s»", (rate, expected) => {
    expect(formatPercent(rate)).toBe(expected);
  });
});

describe("formatRankChangeMessage", () => {
  it.each([
    [6, 4, "+2 места после покупки"],
    [6, 5, "+1 место после покупки"],
    [5, 8, "-3 места после покупки"],
    [24, 12, "+12 мест после покупки"],
    [1, 12, "-11 мест после покупки"],
    [10, 5, "+5 мест после покупки"],
    [22, 1, "+21 место после покупки"],
  ])("для before=%i, after=%i возвращает «%s»", (before, after, expected) => {
    expect(formatRankChangeMessage(before, after)).toBe(expected);
  });
});
