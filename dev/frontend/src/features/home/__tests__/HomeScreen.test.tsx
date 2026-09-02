import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { HomeScreen } from "../HomeScreen";
import { API } from "@/test/handlers";
import { buildReceiptProcessingResult, getHome } from "@/test/fixtures";
import { renderWithProviders } from "@/test/render";
import { server } from "@/test/setup";

describe("HomeScreen", () => {
  it("показывает уровень, XP, экономию, insight и hero challenge", async () => {
    renderWithProviders(<HomeScreen />);

    expect(await screen.findByText("Домовой · уровень 7")).toBeInTheDocument();
    expect(screen.getByText("XP 2100")).toBeInTheDocument();
    expect(screen.getByText(/Весёлый.*5 разных категорий за неделю/)).toBeInTheDocument();
    expect(screen.getByText(/1.?240\s*₽/)).toBeInTheDocument();
    expect(screen.getByText("Экономия за месяц")).toBeInTheDocument();
    expect(screen.getByText(/\+260\s*₽ к прошлому месяцу/)).toBeInTheDocument();
    expect(screen.getByText(/сэкономили/)).toBeInTheDocument();
    expect(screen.getByText("3 покупки за неделю")).toBeInTheDocument();
    expect(screen.getByText("2 / 3")).toBeInTheDocument();
    expect(screen.getByText("+50 XP + 30 баллов")).toBeInTheDocument();
    expect(screen.getByText("Место 5 из 28")).toBeInTheDocument();
    expect(screen.getByText("Приглашено: 3")).toBeInTheDocument();
  });

  it("клик «Почему это мне?» раскрывает explanation", async () => {
    const user = userEvent.setup();
    renderWithProviders(<HomeScreen />);
    await screen.findByText("2 / 3");

    const explanation = "Обычно 2 покупки в неделю (baseline 2), цель — 3 до конца недели.";
    expect(screen.queryByText(explanation)).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Почему это мне?" }));

    expect(await screen.findByText(explanation)).toBeInTheDocument();
  });

  it("клик Simulate вызывает POST .../receipts/simulate и обновляет прогресс", async () => {
    const user = userEvent.setup();
    let homeCalls = 0;
    let simulateCalled = false;

    server.use(
      http.get(`${API}/users/:user_id/home`, () => {
        homeCalls += 1;
        const home = getHome(1);
        if (homeCalls > 1 && home.hero_challenge) {
          return HttpResponse.json({
            ...home,
            hero_challenge: { ...home.hero_challenge, progress: home.hero_challenge.target },
          });
        }
        return HttpResponse.json(home);
      }),
      http.post(`${API}/users/:user_id/receipts/simulate`, () => {
        simulateCalled = true;
        return HttpResponse.json(buildReceiptProcessingResult(1), { status: 201 });
      }),
    );

    renderWithProviders(<HomeScreen />);
    await screen.findByText("2 / 3");

    await user.click(screen.getByRole("button", { name: /simulate new purchase/i }));

    await waitFor(() => expect(simulateCalled).toBe(true));
    expect(await screen.findByText("3 / 3")).toBeInTheDocument();
  });

  it("не создаёт элементов шире 390px", async () => {
    const { container } = renderWithProviders(<HomeScreen />);
    await screen.findByText("2 / 3");

    const tooWide = Array.from(container.querySelectorAll<HTMLElement>("[style]")).filter((el) => {
      const width = Number.parseInt(el.style.width, 10);
      return el.style.width.endsWith("px") && !Number.isNaN(width) && width > 390;
    });
    expect(tooWide).toHaveLength(0);
  });

  it("показывает статус загрузки, пока home ещё не пришёл", () => {
    renderWithProviders(<HomeScreen />);
    expect(screen.getByText("Домовой просыпается…")).toBeInTheDocument();
  });

  it("показывает ошибку, если home не загрузился", async () => {
    server.use(
      http.get(`${API}/users/:user_id/home`, () =>
        HttpResponse.json(
          { error: { code: "internal_error", message: "БД недоступна" } },
          { status: 500 },
        ),
      ),
    );

    renderWithProviders(<HomeScreen />);

    expect(await screen.findByText(/Не получилось загрузить Home/)).toBeInTheDocument();
    expect(screen.getByText(/БД недоступна/)).toBeInTheDocument();
  });

  it("показывает заглушку, если hero_challenge отсутствует", async () => {
    renderWithProviders(<HomeScreen />, ["/?user=3"]);

    expect(await screen.findByText("Домовой · уровень 2")).toBeInTheDocument();
    expect(screen.getByText("Домовой думает над целью недели…")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Почему это мне?" })).not.toBeInTheDocument();
  });
});
