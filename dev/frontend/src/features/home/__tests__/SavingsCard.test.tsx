import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { SavingsCard } from "../components/SavingsCard";
import type { HomeResponse } from "../api";

type Savings = HomeResponse["savings"];
type Category = Savings["top_categories"][number];

const BASE_SAVINGS: Savings = {
  period: "month",
  amount: 1000,
  previous_amount: 900,
  delta: 100,
  discount_amount: 500,
  points_earned: 200,
  points_spent: 50,
  receipts_count: 7,
  top_categories: [],
};

function category(overrides: Partial<Category> & Pick<Category, "category" | "amount">): Category {
  return { items_count: 0, top_products: [], ...overrides };
}

function renderCard(overrides: Partial<Savings> = {}) {
  const savings: Savings = { ...BASE_SAVINGS, ...overrides };
  return render(<SavingsCard savings={savings} justSimulated={false} />);
}

async function openAccordion() {
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "Из чего сложилось" }));
}

describe("SavingsCard — ширина полос топ-категорий считается от максимума", () => {
  it("для одной категории полоса растягивается на 100%", async () => {
    const { container } = renderCard({
      top_categories: [category({ category: "dairy", amount: 260 })],
    });
    await openAccordion();
    const bar = container.querySelector<HTMLElement>(".bg-brand-500");
    expect(bar?.style.width).toBe("100%");
  });

  it("для одинаковых сумм у всех категорий полоса 100%", async () => {
    const { container } = renderCard({
      top_categories: [
        category({ category: "dairy", amount: 200 }),
        category({ category: "bakery", amount: 200 }),
      ],
    });
    await openAccordion();
    const bars = Array.from(container.querySelectorAll<HTMLElement>(".bg-brand-500"));
    expect(bars.map((bar) => bar.style.width)).toEqual(["100%", "100%"]);
  });

  it("для разных сумм младшая категория получает пропорциональную долю от максимума", async () => {
    const { container } = renderCard({
      top_categories: [
        category({ category: "dairy", amount: 400 }),
        category({ category: "bakery", amount: 100 }),
      ],
    });
    await openAccordion();
    const bars = Array.from(container.querySelectorAll<HTMLElement>(".bg-brand-500"));
    expect(bars.map((bar) => bar.style.width)).toEqual(["100%", "25%"]);
  });

  it("без категорий раздел открывается без ошибок", async () => {
    renderCard({ top_categories: [] });
    await openAccordion();
    expect(screen.getByText("Где сэкономили больше всего")).toBeInTheDocument();
  });
});

describe("SavingsCard — значения берутся из пропа savings, не захардкожены", () => {
  it("показывает discount_amount, points_earned, points_spent из пропа", async () => {
    renderCard({ discount_amount: 777, points_earned: 111, points_spent: 22 });
    await openAccordion();
    expect(screen.getByText("777 ₽")).toBeInTheDocument();
    expect(screen.getByText("111")).toBeInTheDocument();
    expect(screen.getByText("22")).toBeInTheDocument();
  });

  it("не показывает строки про баллы, когда касса их не начисляла и не списывала", async () => {
    renderCard({ points_earned: 0, points_spent: 0 });
    await openAccordion();
    expect(screen.getByText("Скидки")).toBeInTheDocument();
    expect(screen.queryByText("Начислено баллов")).not.toBeInTheDocument();
    expect(screen.queryByText("Потрачено баллов")).not.toBeInTheDocument();
  });

  it("показывает только ту строку про баллы, где есть ненулевое значение", async () => {
    renderCard({ points_earned: 40, points_spent: 0 });
    await openAccordion();
    expect(screen.getByText("Начислено баллов")).toBeInTheDocument();
    expect(screen.queryByText("Потрачено баллов")).not.toBeInTheDocument();
  });

  it("для категории вне словаря показывает исходный ключ, не падает", async () => {
    renderCard({ top_categories: [category({ category: "weird_category", amount: 50 })] });
    await openAccordion();
    expect(screen.getByText("weird_category")).toBeInTheDocument();
  });
});

describe("SavingsCard — объяснение цифры", () => {
  it("показывает, по скольким чекам посчитана экономия", () => {
    renderCard({ receipts_count: 12 });
    expect(screen.getByText("По 12 чекам за месяц")).toBeInTheDocument();
  });

  it("склоняет единственный чек", () => {
    renderCard({ receipts_count: 1 });
    expect(screen.getByText("По 1 чеку за месяц")).toBeInTheDocument();
  });

  it("раскрывает формулу экономии по кнопке подсказки", async () => {
    const user = userEvent.setup();
    renderCard();
    await user.click(screen.getByRole("button", { name: "Как считается экономия" }));
    expect(screen.getByRole("note")).toHaveTextContent(
      /разница между обычными ценами и тем, что вы заплатили/,
    );
  });

  it("расшифровывает сумму категории числом позиций и товарами", async () => {
    renderCard({
      top_categories: [
        category({
          category: "bakery",
          amount: 508,
          items_count: 4,
          top_products: ["Батон нарезной", "Круассан"],
        }),
      ],
    });
    await openAccordion();
    expect(screen.getByText("4 позиции со скидкой: Батон нарезной, Круассан")).toBeInTheDocument();
  });

  it("не показывает расшифровку, когда позиций со скидкой нет", async () => {
    renderCard({ top_categories: [category({ category: "bakery", amount: 0 })] });
    await openAccordion();
    expect(screen.queryByText(/позиц/)).not.toBeInTheDocument();
  });
});
