import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Button } from "@/shared/ui/Button";

describe("Button", () => {
  it("рендерит основной вариант по умолчанию и реагирует на клик", async () => {
    const onClick = vi.fn();
    const user = userEvent.setup();
    render(<Button onClick={onClick}>Симулировать покупку</Button>);

    const button = screen.getByRole("button", { name: "Симулировать покупку" });
    expect(button).toHaveClass("bg-brand-700");
    await user.click(button);
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("рендерит недоступное состояние", () => {
    render(<Button disabled>Недоступна</Button>);
    expect(screen.getByRole("button", { name: "Недоступна" })).toBeDisabled();
  });

  it("рендерит акцентную кнопку крупным жирным текстом для контраста", () => {
    render(<Button variant="accent">Акцентная</Button>);
    const button = screen.getByRole("button", { name: "Акцентная" });
    expect(button).toHaveClass("bg-accent-500", "text-lead", "font-bold");
  });
});
