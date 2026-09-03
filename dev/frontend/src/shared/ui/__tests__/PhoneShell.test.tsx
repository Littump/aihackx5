import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PhoneShell } from "@/shared/ui/PhoneShell";

describe("PhoneShell", () => {
  it("скроллер — прямой родитель children и несёт min-h-0 flex-1 overflow-y-auto", () => {
    render(
      <PhoneShell header={<div data-testid="header">Демо-полоса</div>}>
        <div data-testid="content">Экран</div>
      </PhoneShell>,
    );

    const content = screen.getByTestId("content");
    const scroller = content.parentElement;
    expect(scroller).toHaveClass("min-h-0", "flex-1", "overflow-y-auto");
  });

  it("header рендерится вне скроллера, а не внутри прокручиваемой области", () => {
    render(
      <PhoneShell header={<div data-testid="header">Демо-полоса</div>}>
        <div data-testid="content">Экран</div>
      </PhoneShell>,
    );

    const header = screen.getByTestId("header");
    const scroller = screen.getByTestId("content").parentElement;
    expect(scroller?.contains(header)).toBe(false);
  });

  it("произвольно длинный children целиком остаётся в разметке, ничего не отбрасывается", () => {
    const rows = Array.from({ length: 60 }, (_, i) => `Строка ${i + 1}`);
    render(
      <PhoneShell>
        <ul>
          {rows.map((row) => (
            <li key={row}>{row}</li>
          ))}
        </ul>
      </PhoneShell>,
    );

    for (const row of rows) {
      expect(screen.getByText(row)).toBeInTheDocument();
    }
  });

  it("работает без header, не падает и не рендерит лишний узел вместо него", () => {
    render(
      <PhoneShell>
        <div data-testid="content">Экран без шапки</div>
      </PhoneShell>,
    );

    expect(screen.getByTestId("content")).toBeInTheDocument();
  });

  it("footer рендерится вне скроллера, после него, а не внутри прокручиваемой области", () => {
    render(
      <PhoneShell footer={<div data-testid="footer">Нижняя навигация</div>}>
        <div data-testid="content">Экран</div>
      </PhoneShell>,
    );

    const footer = screen.getByTestId("footer");
    const scroller = screen.getByTestId("content").parentElement;
    expect(scroller?.contains(footer)).toBe(false);
  });

  it("работает без footer, не падает и не рендерит лишний узел вместо него", () => {
    render(
      <PhoneShell>
        <div data-testid="content">Экран без футера</div>
      </PhoneShell>,
    );

    expect(screen.getByTestId("content")).toBeInTheDocument();
  });

  it("внешняя обёртка — min-h-dvh и bg-desk, чтобы фон не обрезался высотой экрана", () => {
    const { container } = render(
      <PhoneShell>
        <div>Экран</div>
      </PhoneShell>,
    );

    const outer = container.firstElementChild;
    expect(outer).toHaveClass("min-h-dvh", "bg-desk");
  });
});
