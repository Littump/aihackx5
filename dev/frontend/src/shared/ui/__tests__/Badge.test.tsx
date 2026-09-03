import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Badge } from "@/shared/ui/Badge";

describe("Badge", () => {
  it("тон accent использует безопасную пару accent-50/accent-700", () => {
    render(<Badge>+50 XP</Badge>);
    expect(screen.getByText("+50 XP")).toHaveClass("bg-accent-50", "text-accent-700");
  });

  it("тон accentStrong использует крупный жирный текст для контраста", () => {
    render(<Badge tone="accentStrong">Ново</Badge>);
    expect(screen.getByText("Ново")).toHaveClass(
      "bg-accent-500",
      "text-white",
      "text-lead",
      "font-bold",
    );
  });

  it("тон brand используется для серии/статуса на белой карточке", () => {
    render(<Badge tone="brand">серия 3 нед.</Badge>);
    expect(screen.getByText("серия 3 нед.")).toHaveClass("bg-brand-50", "text-brand-700");
  });
});
