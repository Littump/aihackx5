import { QueryClient } from "@tanstack/react-query";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { HomeScreen } from "@/features/home/HomeScreen";
import { leagueRankChangeKey } from "@/shared/lib/queryKeys";
import { API } from "@/test/handlers";
import { getLeague } from "@/test/fixtures";
import { renderWithProviders } from "@/test/render";
import { server } from "@/test/setup";
import { LeagueScreen } from "../LeagueScreen";

describe("LeagueScreen", () => {
  it("показывает зелёную шапку с дивизионом, неделей, местом/счётом/зоной и «дом vs район»", async () => {
    renderWithProviders(<LeagueScreen />, ["/?user=1"]);
    const league = getLeague(1);

    expect(await screen.findByRole("heading", { name: "Лига домов" })).toBeInTheDocument();
    expect(
      screen.getByText(/Дивизион 2 «серебро» · неделя 31 августа – 6 сентября/),
    ).toBeInTheDocument();

    const header = screen.getByTestId("league-header");
    expect(within(header).getByText(`${league.my_rank} из ${league.size}`)).toBeInTheDocument();
    expect(within(header).getByText(`${league.my_score}`)).toBeInTheDocument();
    expect(within(header).getByText("Повышение")).toBeInTheDocument();

    expect(screen.getByText("Ваш дом против района")).toBeInTheDocument();
    expect(screen.getByText("Пятёрочка на Ленина")).toBeInTheDocument();
    expect(screen.getByText("12%")).toBeInTheDocument();
    expect(screen.getByText("3 из 12")).toBeInTheDocument();
  });

  it("показывает заметку о приватности", async () => {
    renderWithProviders(<LeagueScreen />, ["/?user=1"]);

    expect(
      await screen.findByText(
        /Показываем только псевдонимы и очки\. Ни имён, ни адресов, ни сумм и состава чужих покупок\./,
      ),
    ).toBeInTheDocument();
  });

  it("подсвечивает строку текущего пользователя меткой «Вы»", async () => {
    renderWithProviders(<LeagueScreen />, ["/?user=1"]);

    const myRow = (await screen.findByText("Вы")).closest('[data-testid="league-row"]');
    expect(myRow).not.toBeNull();
    expect(myRow!.textContent).toBe("3Выуровень 7 · зона повышение192");
    expect(myRow!.className).toContain("bg-brand-700");
    expect(myRow!.className).toContain("text-white");

    const otherRow = screen.getByText("Сосед-Бережливый-1").closest('[data-testid="league-row"]');
    expect(otherRow!.textContent).not.toContain("Вы");
  });

  it("в строке участника нет ничего, кроме pseudonym, level, score, rank", async () => {
    renderWithProviders(<LeagueScreen />, ["/?user=1"]);

    const row = (await screen.findByText("Сосед-Бережливый-1")).closest(
      '[data-testid="league-row"]',
    );
    expect(row!.textContent).toBe("1Сосед-Бережливый-1уровень 6204");
  });

  it.each([
    [1, "Повышение"],
    [2, "Безопасная"],
    [3, "Понижение"],
  ])("для user=%i шапка показывает зону «%s»", async (userId, zone) => {
    renderWithProviders(<LeagueScreen />, [`/?user=${userId}`]);

    const header = await screen.findByTestId("league-header");
    expect(within(header).getByText(zone)).toBeInTheDocument();
  });

  it("рендерит все строки лиги из ответа API, а не только часть", async () => {
    renderWithProviders(<LeagueScreen />, ["/?user=1"]);
    const league = getLeague(1);

    await screen.findByRole("heading", { name: "Лига домов" });
    const rows = screen.getAllByTestId("league-row");
    expect(rows).toHaveLength(league.members.length);

    const ranks = rows.map((row) => row.firstElementChild?.textContent);
    expect(ranks).toEqual(Array.from({ length: league.size }, (_, index) => `${index + 1}`));
  });

  it("вставляет разделители зон ровно один раз и в правильной позиции", async () => {
    renderWithProviders(<LeagueScreen />, ["/?user=1"]);
    const league = getLeague(1);

    await screen.findByRole("heading", { name: "Лига домов" });
    const board = screen.getByTestId("leaderboard");

    expect(
      within(board).getAllByText(`Выше — повышение в дивизион ${league.division + 1}`),
    ).toHaveLength(1);
    expect(
      within(board).getAllByText(`Ниже — понижение в дивизион ${league.division - 1}`),
    ).toHaveLength(1);

    const children = Array.from(board.children);
    const promotionIndex = children.findIndex((el) =>
      (el.textContent ?? "").includes("Выше — повышение"),
    );
    const demotionIndex = children.findIndex((el) =>
      (el.textContent ?? "").includes("Ниже — понижение"),
    );

    const rowBeforePromotionDivider = children[promotionIndex - 1];
    expect(rowBeforePromotionDivider.getAttribute("data-testid")).toBe("league-row");
    expect(rowBeforePromotionDivider.firstElementChild?.textContent).toBe(
      `${league.promotion_cutoff}`,
    );

    const rowAfterDemotionDivider = children[demotionIndex + 1];
    expect(rowAfterDemotionDivider.getAttribute("data-testid")).toBe("league-row");
    expect(rowAfterDemotionDivider.firstElementChild?.textContent).toBe(
      `${league.demotion_cutoff}`,
    );
  });

  it("разделители зон следуют за promotion_cutoff/demotion_cutoff из ответа, а не за захардкоженной позицией", async () => {
    const league = getLeague(1);
    const customLeague = {
      ...league,
      promotion_cutoff: 3,
      demotion_cutoff: 10,
      members: league.members.map((member) => ({ ...member, is_me: member.rank === 3 })),
      my_rank: 3,
      my_zone: "promotion" as const,
    };
    server.use(http.get(`${API}/users/:user_id/league`, () => HttpResponse.json(customLeague)));

    renderWithProviders(<LeagueScreen />, ["/?user=1"]);
    await screen.findByRole("heading", { name: "Лига домов" });
    const board = screen.getByTestId("leaderboard");
    const children = Array.from(board.children);

    const promotionIndex = children.findIndex((el) =>
      (el.textContent ?? "").includes("Выше — повышение"),
    );
    const demotionIndex = children.findIndex((el) =>
      (el.textContent ?? "").includes("Ниже — понижение"),
    );

    expect(children[promotionIndex - 1].firstElementChild?.textContent).toBe("3");
    expect(children[demotionIndex + 1].firstElementChild?.textContent).toBe("10");
    expect(within(board).queryAllByText(/Выше — повышение/)).toHaveLength(1);
    expect(within(board).queryAllByText(/Ниже — понижение/)).toHaveLength(1);
  });

  it("зона понижения отображается с полупрозрачным фоном", async () => {
    renderWithProviders(<LeagueScreen />, ["/?user=1"]);
    const league = getLeague(1);

    await screen.findByRole("heading", { name: "Лига домов" });
    const rows = screen.getAllByTestId("league-row");

    const demotionRow = rows[league.demotion_cutoff - 1];
    expect(demotionRow.className).toContain("bg-accent-50/50");

    const safeRow = rows[league.promotion_cutoff];
    expect(safeRow.className).not.toContain("bg-accent-50/50");
  });

  it("показывает скелетон, пока лига ещё не пришла", () => {
    const { container } = renderWithProviders(<LeagueScreen />, ["/?user=1"]);
    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
  });

  it("показывает ошибку с персонажем и повторяет запрос по клику «Повторить»", async () => {
    let calls = 0;
    server.use(
      http.get(`${API}/users/:user_id/league`, () => {
        calls += 1;
        if (calls === 1) {
          return HttpResponse.json(
            { error: { code: "internal_error", message: "БД недоступна" } },
            { status: 500 },
          );
        }
        return HttpResponse.json(getLeague(1));
      }),
    );

    const user = userEvent.setup();
    renderWithProviders(<LeagueScreen />, ["/?user=1"]);

    expect(await screen.findByText("Не получилось загрузить")).toBeInTheDocument();
    expect(screen.queryByText(/БД недоступна/)).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Повторить" }));

    expect(await screen.findByRole("heading", { name: "Лига домов" })).toBeInTheDocument();
    expect(calls).toBe(2);
  });

  it("после Simulate на Home показывает улучшение места стрелкой вверх", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const user = userEvent.setup();

    const home = renderWithProviders(<HomeScreen />, ["/?user=1"], client);
    await screen.findByText(/Уровень 7 · Весёлый/);

    await user.click(screen.getByRole("button", { name: /симулировать покупку/i }));

    await waitFor(() =>
      expect(client.getQueryData(leagueRankChangeKey(1))).toEqual({ before: 6, after: 5 }),
    );
    home.unmount();

    renderWithProviders(<LeagueScreen />, ["/?user=1"], client);

    const indicator = await screen.findByTestId("rank-change");
    expect(indicator.textContent).toContain("+1 место после покупки");
    expect(indicator.querySelector("path")?.getAttribute("d")).toBe("M12 19V5M6 11l6-6 6 6");
  });

  it("показывает ухудшение места стрелкой вниз", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    client.setQueryData(leagueRankChangeKey(1), { before: 5, after: 8 });

    renderWithProviders(<LeagueScreen />, ["/?user=1"], client);

    const indicator = await screen.findByTestId("rank-change");
    expect(indicator.textContent).toContain("-3 места после покупки");
    expect(indicator.querySelector("path")?.getAttribute("d")).toBe("M12 5v14M6 13l6 6 6-6");
  });

  it("не показывает изменение места, если ранг до и после совпадает", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    client.setQueryData(leagueRankChangeKey(1), { before: 5, after: 5 });

    renderWithProviders(<LeagueScreen />, ["/?user=1"], client);

    await screen.findByRole("heading", { name: "Лига домов" });
    expect(screen.queryByTestId("rank-change")).not.toBeInTheDocument();
  });
});
