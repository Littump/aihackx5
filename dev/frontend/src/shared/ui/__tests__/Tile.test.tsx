import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import { Tile } from "@/shared/ui/Tile";

describe("Tile", () => {
  it("с проп to рендерится как ссылка react-router", () => {
    render(
      <MemoryRouter>
        <Tile to="/league" title="Лига" subtitle="6 место из 24" />
      </MemoryRouter>,
    );
    const link = screen.getByRole("link", { name: /Лига/ });
    expect(link).toHaveAttribute("href", "/league");
    expect(screen.getByText("6 место из 24")).toBeInTheDocument();
  });

  it("без to и href рендерится как статичная плитка", () => {
    render(<Tile title="Плитка" />);
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(screen.getByText("Плитка")).toBeInTheDocument();
  });
});
