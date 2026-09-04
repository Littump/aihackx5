import { XP_CHALLENGE, XP_RECEIPT } from "./game_rules";
import { heroChallenge } from "./challenges";
import { DOMOVOY_BY_USER } from "./users";
import type { Receipt, ReceiptProcessingResult, SimulateDraft } from "./types";

const CATEGORIES: SimulateDraft["categories"] = [
  { code: "dairy", products: ["Молоко", "Сыр", "Сметана"] },
  { code: "bakery", products: ["Батон", "Белый хлеб", "Булочка"] },
  { code: "fruits_veg", products: ["Яблоки", "Бананы", "Огурцы"] },
  { code: "meat_fish", products: ["Курица", "Фарш", "Сёмга"] },
  { code: "grocery", products: ["Гречка", "Рис", "Макароны"] },
  { code: "snacks", products: ["Чипсы", "Шоколад", "Печенье"] },
  { code: "drinks", products: ["Вода", "Сок", "Чай"] },
  { code: "alcohol", products: ["Пиво", "Вино", "Сидр"] },
  { code: "household", products: ["Стиральный порошок", "Губки", "Салфетки"] },
  { code: "beauty", products: ["Шампунь", "Зубная паста", "Мыло"] },
  { code: "ready_food", products: ["Роллы", "Пицца", "Сэндвич"] },
  { code: "other", products: ["Батарейки", "Цветы", "Свечи"] },
];

export function getReceipts(): Receipt[] {
  return [
    {
      id: 5001,
      store_id: 101,
      store_name: "Пятёрочка на Ленина",
      purchased_at: "2026-09-02T18:32:00+03:00",
      regular_total: 780,
      paid_total: 640,
      discount_total: 140,
      points_earned: 32,
      points_spent: 0,
      counted: true,
      is_returned: false,
      items: [
        {
          product_name: "Молоко 3.2%",
          category: "dairy",
          qty: 2,
          regular_price: 89,
          paid_price: 79,
          is_promo: true,
        },
      ],
    },
  ];
}

export function buildReceiptProcessingResult(userId: number): ReceiptProcessingResult {
  const hero = heroChallenge(userId);
  const completesHero = hero !== null && hero.progress + 1 >= hero.target;
  const xpDelta = XP_RECEIPT + (completesHero ? XP_CHALLENGE : 0);
  const baseDomovoy = DOMOVOY_BY_USER[userId] ?? DOMOVOY_BY_USER[1];
  return {
    receipt: getReceipts()[0],
    counted: true,
    counted_reason: null,
    xp_delta: xpDelta,
    domovoy: { ...baseDomovoy, xp: baseDomovoy.xp + xpDelta },
    savings_delta: 172,
    challenges: hero
      ? [
          {
            challenge_id: hero.id,
            progress_before: hero.progress,
            progress_after: Math.min(hero.target, hero.progress + 1),
            target: hero.target,
            completed: completesHero,
            reward_points: completesHero ? hero.reward_points : 0,
            reward_xp: completesHero ? hero.reward_xp : 0,
          },
        ]
      : [],
    league_rank_before: 6,
    league_rank_after: 5,
    referral_status: null,
    fraud: { score: 0.1, decision: "approve", signals: [] },
    achievements_unlocked: [],
  };
}

export function getSimulateDraft(userId: number): SimulateDraft {
  const hero = heroChallenge(userId);
  return {
    store_id: 101,
    store_name: "Пятёрочка на Ленина",
    goal:
      hero === null
        ? null
        : {
            type: hero.type,
            category: hero.category,
            title: hero.title,
            progress: hero.progress,
            target: hero.target,
          },
    items: [
      {
        product_name: "Молоко",
        category: "dairy",
        price: 120,
        is_promo: false,
        matches_goal: hero?.category === "dairy",
      },
      {
        product_name: "Батон",
        category: "bakery",
        price: 80,
        is_promo: true,
        matches_goal: false,
      },
      {
        product_name: "Яблоки",
        category: "fruits_veg",
        price: 150,
        is_promo: false,
        matches_goal: false,
      },
    ],
    categories: CATEGORIES,
    default_price: 150,
  };
}
