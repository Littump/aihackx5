import { describe, expect, it } from "vitest";
import { formatPercent, formatWeekRange, zoneForRank } from "../format";

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
