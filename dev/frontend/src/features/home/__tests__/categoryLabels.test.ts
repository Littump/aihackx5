import { describe, expect, it } from "vitest";
import { formatCategoryLabel } from "../categoryLabels";

// 12 категорий из dev/docs/domain-rules.md («Категории (12 макро)») / game_rules.CATEGORIES
const DOMAIN_CATEGORIES = [
  "dairy",
  "bakery",
  "fruits_veg",
  "meat_fish",
  "grocery",
  "snacks",
  "drinks",
  "alcohol",
  "household",
  "beauty",
  "ready_food",
  "other",
] as const;

describe("formatCategoryLabel", () => {
  it.each(DOMAIN_CATEGORIES)(
    "для категории «%s» из domain-rules возвращает непустую русскую подпись",
    (category) => {
      const label = formatCategoryLabel(category);
      expect(label).not.toBe(category);
      expect(label).toMatch(/[а-яё]/i);
    },
  );

  it("для неизвестной категории возвращает исходный ключ, а не падает и не пустую строку", () => {
    expect(formatCategoryLabel("unknown_category")).toBe("unknown_category");
  });
});
