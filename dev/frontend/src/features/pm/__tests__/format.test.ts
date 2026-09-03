import { describe, expect, it } from "vitest";
import {
  decisionBadgeClass,
  decisionLabel,
  formatDateTime,
  formatPercent,
  mechanicLabel,
} from "../format";
import type { FraudDecision, PmUserResponse } from "../api";

describe("decisionLabel и decisionBadgeClass", () => {
  it.each<[FraudDecision, string]>([
    ["approve", "Одобрено"],
    ["hold", "Отложено"],
    ["block", "Заблокировано"],
  ])("для решения %s возвращает подпись «%s»", (decision, label) => {
    expect(decisionLabel(decision)).toBe(label);
    expect(decisionBadgeClass(decision)).toMatch(/^bg-/);
  });

  it("для block и approve использует разные классы бейджа", () => {
    expect(decisionBadgeClass("block")).not.toBe(decisionBadgeClass("approve"));
  });
});

describe("mechanicLabel", () => {
  it.each<[PmUserResponse["recommended_mechanic"]["mechanic"], string]>([
    ["challenge", "Челлендж"],
    ["league", "Лига"],
    ["referral", "Рефералы"],
  ])("для механики %s возвращает подпись «%s»", (mechanic, label) => {
    expect(mechanicLabel(mechanic)).toBe(label);
  });
});

describe("formatPercent", () => {
  it.each([
    [0.32, "32%"],
    [0, "0%"],
    [1, "100%"],
  ])("округляет %f до «%s»", (rate, expected) => {
    expect(formatPercent(rate)).toBe(expected);
  });
});

describe("formatDateTime", () => {
  it("форматирует ISO-дату в дату и время по-русски", () => {
    expect(formatDateTime("2026-09-01T14:00:00+03:00")).toBe("1 сентября в 14:00");
  });
});
