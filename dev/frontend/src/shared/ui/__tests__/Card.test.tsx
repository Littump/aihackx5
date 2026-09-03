import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Card } from "@/shared/ui/Card";

describe("Card", () => {
  it("рендерит поверхность по новым токенам и переданное содержимое", () => {
    render(<Card>Содержимое карточки</Card>);
    const card = screen.getByText("Содержимое карточки");
    expect(card).toHaveClass("rounded-card", "bg-surface", "shadow-card");
  });

  it("добавляет переданный className к базовым классам", () => {
    render(<Card className="mt-4">Ещё карточка</Card>);
    expect(screen.getByText("Ещё карточка")).toHaveClass("rounded-card", "mt-4");
  });
});
