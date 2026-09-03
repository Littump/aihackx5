import type { LeagueResponse } from "./api";

export type LeagueZone = LeagueResponse["my_zone"];

const ZONE_LABELS: Record<LeagueZone, string> = {
  promotion: "Повышение",
  safe: "Стабильно",
  demotion: "Понижение",
};

const ZONE_BADGE_CLASSES: Record<LeagueZone, string> = {
  promotion: "bg-legacy-brand-100 text-legacy-brand-600",
  safe: "bg-bg text-text-secondary border border-border",
  demotion: "bg-accent-100 text-legacy-accent-600",
};

const ZONE_ROW_CLASSES: Record<LeagueZone, string> = {
  promotion: "border-l-4 border-legacy-brand-600",
  safe: "border-l-4 border-border",
  demotion: "border-l-4 border-legacy-accent-600",
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

export function zoneBadgeClass(zone: LeagueZone): string {
  return ZONE_BADGE_CLASSES[zone];
}

export function zoneRowClass(zone: LeagueZone): string {
  return ZONE_ROW_CLASSES[zone];
}

export function formatWeekRange(weekStart: string, weekEnd: string): string {
  const formatter = new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "long" });
  return `${formatter.format(new Date(weekStart))} – ${formatter.format(new Date(weekEnd))}`;
}

export function formatPercent(rate: number): string {
  return `${Math.round(rate * 100)}%`;
}
