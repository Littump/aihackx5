import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import { QuickLinks } from "../components/QuickLinks";
import type { HomeResponse } from "../api";

const LEAGUE: HomeResponse["league"] = { division: 1, rank: 5, size: 28, zone: "safe" };
const REFERRAL: HomeResponse["referral"] = {
  code: "DOM-1F2B",
  invited_count: 3,
  rewarded_count: 1,
};

function renderTiles(
  league: HomeResponse["league"],
  referral: HomeResponse["referral"],
  initialEntries: string[],
) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <QuickLinks league={league} referral={referral} />
    </MemoryRouter>,
  );
}

describe("QuickLinks", () => {
  it("ссылки Лига/Соседи сохраняют query-параметр ?user= текущего URL", () => {
    renderTiles(LEAGUE, REFERRAL, ["/?user=7"]);
    expect(screen.getByRole("link", { name: /Лига/ })).toHaveAttribute("href", "/league?user=7");
    expect(screen.getByRole("link", { name: /Соседи/ })).toHaveAttribute(
      "href",
      "/referral?user=7",
    );
  });

  it("с лигой показывает «Место N из M»", () => {
    renderTiles(LEAGUE, REFERRAL, ["/?user=1"]);
    expect(screen.getByText("Место 5 из 28")).toBeInTheDocument();
  });

  it("без лиги показывает «Пока нет лиги»", () => {
    renderTiles(null, REFERRAL, ["/?user=1"]);
    expect(screen.getByText("Пока нет лиги")).toBeInTheDocument();
  });

  it("показывает «Приглашено: N» из referral", () => {
    renderTiles(LEAGUE, { ...REFERRAL, invited_count: 9 }, ["/?user=1"]);
    expect(screen.getByText("Приглашено: 9")).toBeInTheDocument();
  });
});
