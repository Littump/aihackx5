import type { DomovoyState, SavingsSummary, UserSummary } from "./types";

export const USERS: UserSummary[] = [
  { id: 1, pseudonym: "Хомяк-Запасливый", segment: "regular_mid", level: 7 },
  { id: 2, pseudonym: "Сова-Полуночница", segment: "heavy", level: 4 },
  { id: 3, pseudonym: "Ёжик-Новичок", segment: "light", level: 2 },
];

export const DOMOVOY_BY_USER: Record<number, DomovoyState> = {
  1: {
    xp: 2100,
    level: 7,
    xp_to_next_level: 700,
    mood: "cheerful",
    mood_reason: "5 разных категорий за неделю",
    streak_weeks: 3,
    items: ["зелёная шапка", "лампа-светлячок"],
  },
  2: {
    xp: 740,
    level: 4,
    xp_to_next_level: 260,
    mood: "healthy",
    mood_reason: "овощи и молочка — треть корзины",
    streak_weeks: 1,
    items: ["плетёная корзина"],
  },
  3: {
    xp: 150,
    level: 2,
    xp_to_next_level: 150,
    mood: "sleepy",
    mood_reason: "нет покупок больше недели",
    streak_weeks: 0,
    items: [],
  },
};

export const SAVINGS_BY_USER: Record<number, SavingsSummary> = {
  1: {
    period: "month",
    amount: 1240,
    previous_amount: 980,
    delta: 260,
    discount_amount: 800,
    points_earned: 300,
    points_spent: 140,
    top_categories: [
      { category: "dairy", amount: 420 },
      { category: "fruits_veg", amount: 310 },
      { category: "bakery", amount: 180 },
    ],
  },
  2: {
    period: "month",
    amount: 860,
    previous_amount: 790,
    delta: 70,
    discount_amount: 540,
    points_earned: 210,
    points_spent: 60,
    top_categories: [
      { category: "meat_fish", amount: 260 },
      { category: "grocery", amount: 200 },
    ],
  },
  3: {
    period: "month",
    amount: 120,
    previous_amount: 0,
    delta: 120,
    discount_amount: 80,
    points_earned: 20,
    points_spent: 0,
    top_categories: [{ category: "snacks", amount: 60 }],
  },
};

export function getUserSummary(userId: number): UserSummary {
  return USERS.find((user) => user.id === userId) ?? USERS[0];
}
