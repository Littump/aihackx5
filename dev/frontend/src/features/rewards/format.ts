import { formatNumber, pluralize } from "@/shared/lib/format";

const dateFormatter = new Intl.DateTimeFormat("ru-RU", {
  day: "numeric",
  month: "long",
  timeZone: "Europe/Moscow",
});

const POINT_FORMS: [string, string, string] = ["балл", "балла", "баллов"];

export function pluralizePoints(value: number): string {
  return pluralize(value, POINT_FORMS);
}

export function formatPoints(value: number): string {
  return `${formatNumber(value)} ${pluralizePoints(value)}`;
}

export function formatSignedPoints(value: number): string {
  const sign = value > 0 ? "+" : value < 0 ? "−" : "";
  return `${sign}${formatPoints(Math.abs(value))}`;
}

export function formatSignedXp(value: number): string {
  const sign = value > 0 ? "+" : value < 0 ? "−" : "";
  return `${sign}${formatNumber(Math.abs(value))} XP`;
}

export function formatEventDate(isoDate: string): string {
  return dateFormatter.format(new Date(isoDate));
}

export function formatRulePoints(pointsMin: number, pointsMax: number): string | null {
  if (pointsMax === 0) return null;
  if (pointsMin === pointsMax) return `+${formatPoints(pointsMax)}`;
  return `+${formatNumber(pointsMin)}…${formatPoints(pointsMax)}`;
}
