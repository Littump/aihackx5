const CATEGORY_LABEL: Record<string, string> = {
  dairy: "Молочное",
  bakery: "Выпечка",
  fruits_veg: "Овощи и фрукты",
  meat_fish: "Мясо и рыба",
  grocery: "Бакалея",
  snacks: "Снеки",
  drinks: "Напитки",
  alcohol: "Алкоголь",
  household: "Хозтовары",
  beauty: "Красота и уход",
  ready_food: "Готовая еда",
  other: "Другое",
};

export function formatCategoryLabel(category: string): string {
  return CATEGORY_LABEL[category] ?? category;
}
