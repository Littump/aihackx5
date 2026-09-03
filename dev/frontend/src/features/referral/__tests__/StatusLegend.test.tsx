import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusLegend } from "../components/StatusLegend";

const EXPECTED_TEXTS = [
  "ожидает",
  "первая покупка",
  "выполнил условия",
  "на проверке",
  "награда получена",
  "отклонён",
];

describe("StatusLegend", () => {
  it("показывает все 6 статусов контракта с их текстом", () => {
    render(<StatusLegend />);

    for (const text of EXPECTED_TEXTS) {
      expect(screen.getByText(text)).toBeInTheDocument();
    }
  });

  it("у каждого из 6 статусов уникальная SVG-иконка, не одна и та же с другим цветом", () => {
    const { container } = render(<StatusLegend />);

    const iconPaths = Array.from(container.querySelectorAll("svg")).map((svg) => svg.innerHTML);
    expect(iconPaths).toHaveLength(EXPECTED_TEXTS.length);
    expect(new Set(iconPaths).size).toBe(iconPaths.length);
  });
});
