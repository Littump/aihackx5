import type { LeagueResponse } from "./api";

export type LeagueZone = LeagueResponse["my_zone"];

const ZONE_LABELS: Record<LeagueZone, string> = {
  promotion: "Повышение",
  safe: "Безопасная",
  demotion: "Понижение",
};

export function zoneForRank(
  rank: number,
  promotionCutoff: number,
  demotionCutoff: number,
): LeagueZone {
  if (rank <= promotionCutoff) return "promotion";
  if (rank >= demotionCutoff) return "demotion";
  return "safe";
}

export function zoneLabel(zone: LeagueZone): string {
  return ZONE_LABELS[zone];
}

export function zoneRowClass(zone: LeagueZone): string {
  return zone === "demotion" ? "bg-accent-50/50" : "";
}

export function isPromotionBoundary(rank: number, promotionCutoff: number): boolean {
  return rank === promotionCutoff;
}

export function isDemotionBoundary(rank: number, demotionCutoff: number): boolean {
  return rank === demotionCutoff;
}

export function formatWeekRange(weekStart: string, weekEnd: string): string {
  const formatter = new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
    timeZone: "Europe/Moscow",
  });
  return `${formatter.format(new Date(weekStart))} – ${formatter.format(new Date(weekEnd))}`;
}

export function formatPercent(rate: number): string {
  return `${Math.round(rate * 100)}%`;
}

function placesWord(count: number): string {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod100 >= 11 && mod100 <= 14) return "мест";
  if (mod10 === 1) return "место";
  if (mod10 >= 2 && mod10 <= 4) return "места";
  return "мест";
}

export function formatRankChangeMessage(before: number, after: number): string {
  const delta = before - after;
  const count = Math.abs(delta);
  const sign = delta > 0 ? "+" : "-";
  return `${sign}${count} ${placesWord(count)} после покупки`;
}
