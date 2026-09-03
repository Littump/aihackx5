import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ListRow } from "@/shared/ui/ListRow";

describe("ListRow", () => {
  it("рендерит заголовок, подпись и значение", () => {
    render(<ListRow title="Сосед у лифта" subtitle="уровень 7" value="377" />);
    expect(screen.getByText("Сосед у лифта")).toBeInTheDocument();
    expect(screen.getByText("уровень 7")).toBeInTheDocument();
    expect(screen.getByText("377")).toBeInTheDocument();
  });

  it("выделенная строка «Вы» получает тёмный фон", () => {
    render(<ListRow title="Вы" value="418" highlighted />);
    expect(screen.getByText("Вы").closest("div")).toHaveClass("bg-brand-700", "text-white");
  });

  it("кликабельная строка рендерится как button и реагирует на клик", async () => {
    const onClick = vi.fn();
    const user = userEvent.setup();
    render(<ListRow title="Взять цель" onClick={onClick} />);

    const row = screen.getByRole("button", { name: /Взять цель/ });
    await user.click(row);
    expect(onClick).toHaveBeenCalledOnce();
  });
});
