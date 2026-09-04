import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import { LinkButton } from "@/shared/ui/LinkButton";

describe("LinkButton", () => {
  it("рендерится как ссылка react-router с нужным href", () => {
    render(
      <MemoryRouter>
        <LinkButton to="/referral?user=3">Позвать соседа</LinkButton>
      </MemoryRouter>,
    );
    const link = screen.getByRole("link", { name: "Позвать соседа" });
    expect(link).toHaveAttribute("href", "/referral?user=3");
  });

  it("вариант secondary визуально отличается от primary", () => {
    render(
      <MemoryRouter>
        <LinkButton to="/" variant="secondary">
          Вторичная
        </LinkButton>
      </MemoryRouter>,
    );
    const link = screen.getByRole("link", { name: "Вторичная" });
    expect(link.className).toContain("border-brand-600");
  });
});
