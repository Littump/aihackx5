import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import { BottomNav } from "@/shared/ui/BottomNav";

function renderNav(initialEntries: string[]) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <BottomNav />
    </MemoryRouter>,
  );
}

describe("BottomNav", () => {
  it("рендерит ровно 4 пункта с подписями Дом, Цель, Лига, Соседи", () => {
    renderNav(["/"]);
    const links = screen.getAllByRole("link");
    expect(links).toHaveLength(4);
    expect(screen.getByText("Дом")).toBeInTheDocument();
    expect(screen.getByText("Цель")).toBeInTheDocument();
    expect(screen.getByText("Лига")).toBeInTheDocument();
    expect(screen.getByText("Соседи")).toBeInTheDocument();
  });

  it("нигде нет старой подписи «Челлендж»", () => {
    renderNav(["/"]);
    expect(screen.queryByText("Челлендж")).not.toBeInTheDocument();
    expect(screen.queryByText(/challenge/i)).not.toBeInTheDocument();
  });

  it("каждый пункт содержит непустой валидный inline SVG", () => {
    renderNav(["/"]);
    const links = screen.getAllByRole("link");
    for (const link of links) {
      const svg = link.querySelector("svg");
      expect(svg).toBeInTheDocument();
      expect(svg?.querySelectorAll("path, circle").length ?? 0).toBeGreaterThan(0);
    }
  });

  it("активный пункт получает aria-current=page и акцентный класс", () => {
    renderNav(["/challenge"]);
    const activeLink = screen.getByRole("link", { name: /Цель/ });
    expect(activeLink).toHaveAttribute("aria-current", "page");
    expect(activeLink).toHaveClass("font-semibold", "text-brand-600");
  });

  it("неактивные пункты не получают aria-current и окрашены нейтрально", () => {
    renderNav(["/challenge"]);
    const homeLink = screen.getByRole("link", { name: /Дом/ });
    expect(homeLink).not.toHaveAttribute("aria-current");
    expect(homeLink).toHaveClass("text-ink-500");
  });

  it("переносит текущие query-параметры в каждую ссылку, чтобы не терять демо-пользователя", () => {
    renderNav(["/challenge?user=3"]);
    for (const link of screen.getAllByRole("link")) {
      expect(link).toHaveAttribute("href", expect.stringContaining("?user=3"));
    }
  });

  it("без query-параметров ссылки остаются чистыми путями", () => {
    renderNav(["/"]);
    expect(screen.getByRole("link", { name: /Лига/ })).toHaveAttribute("href", "/league");
  });

  it("пункт «Дом» активен только на точном /, не на вложенных путях", () => {
    renderNav(["/league"]);
    const homeLink = screen.getByRole("link", { name: /Дом/ });
    expect(homeLink).not.toHaveAttribute("aria-current");
    const leagueLink = screen.getByRole("link", { name: /Лига/ });
    expect(leagueLink).toHaveAttribute("aria-current", "page");
  });
});
