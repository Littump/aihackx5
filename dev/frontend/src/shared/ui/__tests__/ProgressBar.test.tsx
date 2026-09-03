import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProgressBar } from "@/shared/ui/ProgressBar";

describe("ProgressBar", () => {
  it("светлый тон используется по умолчанию", () => {
    render(<ProgressBar value={2} max={3} />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveClass("bg-brand-50");
    expect(bar).toHaveAttribute("aria-valuenow", "2");
    expect(bar).toHaveAttribute("aria-valuemax", "3");
  });

  it("тёмный тон подходит для зелёной карточки", () => {
    render(<ProgressBar value={1} max={2} tone="dark" />);
    expect(screen.getByRole("progressbar")).toHaveClass("bg-brand-700");
  });
});
