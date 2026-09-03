import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PaidLimitCard } from "../components/PaidLimitCard";

describe("PaidLimitCard", () => {
  it("показывает прогресс лимита месяца из пропов, а не хардкод", () => {
    render(<PaidLimitCard paidThisMonth={3} paidLimitMonth={5} />);

    expect(screen.getByText("выплачено 3 из 5")).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "3");
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuemax", "5");
  });

  it("не падает при нулевом месячном лимите", () => {
    render(<PaidLimitCard paidThisMonth={0} paidLimitMonth={0} />);

    expect(screen.getByText("выплачено 0 из 0")).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "0");
  });
});
