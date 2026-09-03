import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusChip } from "@/shared/ui/StatusChip";

describe("StatusChip", () => {
  it("показывает текст рядом с иконкой, а не только цвет", () => {
    render(<StatusChip status="success" label="успешно" />);
    const chip = screen.getByText("успешно");
    expect(chip).toBeInTheDocument();
    expect(chip.closest("span")?.querySelector("svg")).toBeInTheDocument();
  });

  it.each([
    ["success", "bg-brand-50"],
    ["inProgress", "bg-accent-50"],
    ["failed", "bg-canvas"],
    ["neutral", "bg-canvas"],
  ] as const)("статус %s получает свой тон %s", (status, expectedClass) => {
    render(<StatusChip status={status} label={status} />);
    expect(screen.getByText(status)).toHaveClass(expectedClass);
  });
});
