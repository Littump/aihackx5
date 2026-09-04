import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { SavingsCard } from "../components/SavingsCard";
import type { HomeResponse } from "../api";

type Savings = HomeResponse["savings"];

const BASE_SAVINGS: Savings = {
  period: "month",
  amount: 1000,
  previous_amount: 900,
  delta: 100,
  discount_amount: 500,
  points_earned: 200,
  points_spent: 50,
  top_categories: [],
};

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
    const { container } = renderCard({ top_categories: [{ category: "dairy", amount: 260 }] });
    await openAccordion();
    const bar = container.querySelector<HTMLElement>(".bg-brand-500");
    expect(bar?.style.width).toBe("100%");
  });

  it("для одинаковых сумм у всех категорий полоса 100%", async () => {
    const { container } = renderCard({
      top_categories: [
        { category: "dairy", amount: 200 },
        { category: "bakery", amount: 200 },
      ],
    });
    await openAccordion();
    const bars = Array.from(container.querySelectorAll<HTMLElement>(".bg-brand-500"));
    expect(bars.map((bar) => bar.style.width)).toEqual(["100%", "100%"]);
  });

  it("для разных сумм младшая категория получает пропорциональную долю от максимума", async () => {
    const { container } = renderCard({
      top_categories: [
        { category: "dairy", amount: 400 },
        { category: "bakery", amount: 100 },
      ],
    });
    await openAccordion();
    const bars = Array.from(container.querySelectorAll<HTMLElement>(".bg-brand-500"));
    expect(bars.map((bar) => bar.style.width)).toEqual(["100%", "25%"]);
  });

  it("без категорий раздел «Топ-категории» открывается без ошибок", async () => {
    renderCard({ top_categories: [] });
    await openAccordion();
    expect(screen.getByText("Топ-категории")).toBeInTheDocument();
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

  it("для категории вне словаря показывает исходный ключ, не падает", async () => {
    renderCard({ top_categories: [{ category: "weird_category", amount: 50 }] });
    await openAccordion();
    expect(screen.getByText("weird_category")).toBeInTheDocument();
  });
});
