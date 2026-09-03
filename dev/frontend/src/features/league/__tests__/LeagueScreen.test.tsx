import { QueryClient } from "@tanstack/react-query";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { HomeScreen } from "@/features/home/HomeScreen";
import { leagueRankChangeKey } from "@/shared/lib/queryKeys";
import { API } from "@/test/handlers";
import { renderWithProviders } from "@/test/render";
import { server } from "@/test/setup";
import { LeagueScreen } from "../LeagueScreen";

describe("LeagueScreen", () => {
  it("показывает дивизион, неделю, моё место и «дом vs район»", async () => {
    renderWithProviders(<LeagueScreen />, ["/?user=1"]);

    expect(await screen.findByText("серебро")).toBeInTheDocument();
    expect(screen.getByText("Дивизион 2")).toBeInTheDocument();
    expect(screen.getByText(/31 августа.*6 сентября/)).toBeInTheDocument();
    expect(screen.getByText(/Место 3/)).toBeInTheDocument();
    expect(screen.getByText("из 24")).toBeInTheDocument();
    expect(screen.getByText("Очки: 192")).toBeInTheDocument();

    expect(screen.getByText("Дом vs район")).toBeInTheDocument();
    expect(screen.getByText("Пятёрочка на Ленина")).toBeInTheDocument();
    expect(screen.getByText("12%")).toBeInTheDocument();
    expect(screen.getByText("Место среди домов района: 3 из 12")).toBeInTheDocument();
  });

  it("подсвечивает строку текущего пользователя меткой «Вы»", async () => {
    renderWithProviders(<LeagueScreen />, ["/?user=1"]);

    const myRow = (await screen.findByText("Хомяк-Запасливый")).closest(
      '[data-testid="league-row"]',
    );
    expect(myRow).not.toBeNull();
    expect(myRow!.textContent).toBe("3Хомяк-ЗапасливыйВыур. 7192");

    const otherRow = screen.getByText("Сосед-Бережливый-1").closest('[data-testid="league-row"]');
    expect(otherRow!.textContent).not.toContain("Вы");
  });

  it("в строке участника нет ничего, кроме pseudonym, level, score, rank", async () => {
    renderWithProviders(<LeagueScreen />, ["/?user=1"]);

    const row = (await screen.findByText("Сосед-Бережливый-1")).closest(
      '[data-testid="league-row"]',
    );
    expect(row!.textContent).toBe("1Сосед-Бережливый-1ур. 6204");
  });

  it.each([
    [1, "Повышение"],
    [2, "Стабильно"],
    [3, "Понижение"],
  ])("для user=%i карточка «моё место» показывает зону «%s»", async (userId, zoneLabel) => {
    renderWithProviders(<LeagueScreen />, [`/?user=${userId}`]);

    const heading = await screen.findByRole("heading", { name: "серебро" });
    const headerRow = heading.closest("div")?.parentElement;
    expect(headerRow).not.toBeNull();
    expect(within(headerRow!).getByText(zoneLabel)).toBeInTheDocument();
  });

  it("подсвечивает строки списка цветом зоны: повышение / стабильно / понижение", async () => {
    renderWithProviders(<LeagueScreen />, ["/?user=1"]);
    await screen.findByText("серебро");

    const rows = screen.getAllByTestId("league-row");
    expect(rows).toHaveLength(24);

    expect(rows[0].className).toContain("border-brand-600");
    expect(rows[9].className).toContain("border-border");
    expect(rows[9].className).not.toContain("border-brand-600");
    expect(rows[9].className).not.toContain("border-accent-600");
    expect(rows[21].className).toContain("border-accent-600");
  });

  it("показывает состояние загрузки, пока лига ещё не пришла", () => {
    renderWithProviders(<LeagueScreen />, ["/?user=1"]);
    expect(screen.getByText("Загружаем таблицу лиги…")).toBeInTheDocument();
  });

  it("показывает ошибку, если лига не загрузилась", async () => {
    server.use(
      http.get(`${API}/users/:user_id/league`, () =>
        HttpResponse.json(
          { error: { code: "internal_error", message: "БД недоступна" } },
          { status: 500 },
        ),
      ),
    );

    renderWithProviders(<LeagueScreen />, ["/?user=1"]);

    expect(await screen.findByText(/Не получилось загрузить лигу/)).toBeInTheDocument();
    expect(screen.getByText(/БД недоступна/)).toBeInTheDocument();
  });

  it("после Simulate на Home показывает изменение места в League", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const user = userEvent.setup();

    const home = renderWithProviders(<HomeScreen />, ["/?user=1"], client);
    await screen.findByText("Домовой · уровень 7");

    await user.click(screen.getByRole("button", { name: /simulate new purchase/i }));

    await waitFor(() =>
      expect(client.getQueryData(leagueRankChangeKey(1))).toEqual({ before: 6, after: 5 }),
    );
    home.unmount();

    renderWithProviders(<LeagueScreen />, ["/?user=1"], client);

    expect(await screen.findByText(/Место изменилось: 6 → 5/)).toBeInTheDocument();
  });

  it("показывает ухудшение места стрелкой вниз и другим цветом", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    client.setQueryData(leagueRankChangeKey(1), { before: 5, after: 8 });

    renderWithProviders(<LeagueScreen />, ["/?user=1"], client);

    const message = await screen.findByText(/Место изменилось: 5 → 8/);
    expect(message.textContent).toContain("▼");
    expect(message.className).toContain("text-accent-600");
  });

  it("не показывает изменение места, если ранг до и после совпадает", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    client.setQueryData(leagueRankChangeKey(1), { before: 5, after: 5 });

    renderWithProviders(<LeagueScreen />, ["/?user=1"], client);

    await screen.findByText("серебро");
    expect(screen.queryByText(/Место изменилось/)).not.toBeInTheDocument();
  });
});
