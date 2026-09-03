import type { components } from "@/shared/api/schema";

export type DomovoyMood = components["schemas"]["DomovoyState"]["mood"];

export const MOOD_LABEL: Record<DomovoyMood, string> = {
  cheerful: "Весёлый",
  cozy: "Уютный",
  healthy: "Бодрый",
  bored: "Скучающий",
  sleepy: "Сонный",
};
