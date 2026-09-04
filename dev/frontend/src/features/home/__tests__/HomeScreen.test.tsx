import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";
import { HomeScreen } from "../HomeScreen";
import { API } from "@/test/handlers";
import { buildReceiptProcessingResult, getHome } from "@/test/fixtures";
import { renderWithProviders } from "@/test/render";
import { server } from "@/test/setup";

describe("HomeScreen", () => {
  it("показывает уровень, XP, экономию, insight и hero challenge", async () => {
    renderWithProviders(<HomeScreen />);

    expect(await screen.findByText("Домовой")).toBeInTheDocument();
    expect(screen.getByText("2100 XP")).toBeInTheDocument();
    expect(screen.getByText(/Весёлый.*5 разных категорий за неделю/)).toBeInTheDocument();
    expect(screen.getByText(/1.?240\s*₽/)).toBeInTheDocument();
    expect(screen.getByText("Экономия за месяц")).toBeInTheDocument();
    expect(screen.getByText(/\+260\s*₽ к прошлому месяцу/)).toBeInTheDocument();
    expect(screen.getByText(/Домовой заметил/)).toBeInTheDocument();
    expect(screen.getByText("3 покупки за неделю")).toBeInTheDocument();
    expect(screen.getByText("2 из 3")).toBeInTheDocument();
    expect(screen.getByText("+50 XP и 30 баллов")).toBeInTheDocument();
    expect(screen.getByText("Место 5 из 28")).toBeInTheDocument();
    expect(screen.getByText("Приглашено: 3")).toBeInTheDocument();
  });

  it("инсайт отображается после карточки цели недели", async () => {
    renderWithProviders(<HomeScreen />);
    await screen.findByText("2 из 3");

    const heading = await screen.findByText("Домовой заметил");
    const goalHeading = screen.getByText("Цель недели");
    const position = goalHeading.compareDocumentPosition(heading);
    expect(position & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("клик «Почему это мне?» раскрывает explanation", async () => {
    const user = userEvent.setup();
    renderWithProviders(<HomeScreen />);
    await screen.findByText("2 из 3");

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
    await screen.findByText("2 из 3");

    await user.click(screen.getByRole("button", { name: /симулировать покупку/i }));

    await waitFor(() => expect(simulateCalled).toBe(true));
    expect(await screen.findByText("3 из 3")).toBeInTheDocument();
  });

  it("не создаёт элементов шире 390px", async () => {
    const { container } = renderWithProviders(<HomeScreen />);
    await screen.findByText("2 из 3");

    const tooWide = Array.from(container.querySelectorAll<HTMLElement>("[style]")).filter((el) => {
      const width = Number.parseInt(el.style.width, 10);
      return el.style.width.endsWith("px") && !Number.isNaN(width) && width > 390;
    });
    expect(tooWide).toHaveLength(0);
  });

  it("показывает скелетон, пока home ещё не пришёл", () => {
    const { container } = renderWithProviders(<HomeScreen />);
    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
  });

  it("показывает ошибку с персонажем и повторяет запрос по клику «Повторить»", async () => {
    let calls = 0;
    server.use(
      http.get(`${API}/users/:user_id/home`, () => {
        calls += 1;
        if (calls === 1) {
          return HttpResponse.json(
            { error: { code: "internal_error", message: "БД недоступна" } },
            { status: 500 },
          );
        }
        return HttpResponse.json(getHome(1));
      }),
    );

    const user = userEvent.setup();
    renderWithProviders(<HomeScreen />);

    expect(await screen.findByText("Не получилось загрузить")).toBeInTheDocument();
    expect(screen.queryByText(/БД недоступна/)).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Повторить" }));

    expect(await screen.findByText("Домовой")).toBeInTheDocument();
    expect(calls).toBe(2);
  });

  it("показывает заглушку с персонажем и ссылкой на соседей, если hero_challenge отсутствует", async () => {
    renderWithProviders(<HomeScreen />, ["/?user=3"]);

    expect(await screen.findByText(/Уровень 2 · Сонный/)).toBeInTheDocument();
    expect(screen.getByText("Домовой думает над целью недели…")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Почему это мне?" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Позвать соседа" })).toHaveAttribute(
      "href",
      "/referral?user=3",
    );
  });

  it("клик «Из чего сложилось» раскрывает скидки, баллы и топ-категории", async () => {
    const user = userEvent.setup();
    renderWithProviders(<HomeScreen />);
    await screen.findByText("2 из 3");

    expect(screen.queryByText("Скидки")).not.toBeInTheDocument();

    const toggle = screen.getByRole("button", { name: "Из чего сложилось" });
    expect(toggle).toHaveAttribute("aria-expanded", "false");

    await user.click(toggle);

    expect(toggle).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("Скидки")).toBeInTheDocument();
    expect(screen.getByText("800 ₽")).toBeInTheDocument();
    expect(screen.getByText("Начислено баллов")).toBeInTheDocument();
    expect(screen.getByText("300")).toBeInTheDocument();
    expect(screen.getByText("Потрачено баллов")).toBeInTheDocument();
    expect(screen.getByText("140")).toBeInTheDocument();
    expect(screen.getByText("Топ-категории")).toBeInTheDocument();
    expect(screen.getByText("Молочное")).toBeInTheDocument();
    expect(screen.getByText("420 ₽")).toBeInTheDocument();
    expect(screen.getByText("Овощи и фрукты")).toBeInTheDocument();
    expect(screen.getByText("310 ₽")).toBeInTheDocument();

    await user.click(toggle);

    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByText("Скидки")).not.toBeInTheDocument();
  });

  it("кнопка симуляции подписана по-русски, без англицизмов в видимом тексте", async () => {
    renderWithProviders(<HomeScreen />);
    await screen.findByText("2 из 3");

    expect(screen.getByRole("button", { name: "Симулировать покупку" })).toBeInTheDocument();
    expect(screen.queryByText(/simulate/i)).not.toBeInTheDocument();
  });

  it("после симуляции подсвечиваются конкретные числа (XP, экономия, прогресс цели), а не карточки целиком", async () => {
    const user = userEvent.setup();
    const { container } = renderWithProviders(<HomeScreen />);
    await screen.findByText("2 из 3");

    expect(container.querySelector(".animate-glow")).not.toBeInTheDocument();

    const cardsBefore = Array.from(container.querySelectorAll(".rounded-card"));
    expect(cardsBefore.some((card) => card.className.includes("bg-accent"))).toBe(false);

    await user.click(screen.getByRole("button", { name: /симулировать покупку/i }));

    await waitFor(() => {
      const glowing = container.querySelectorAll(".animate-glow");
      expect(glowing).toHaveLength(3);
      glowing.forEach((el) => expect(el.tagName).toBe("SPAN"));
    });

    const cardsAfter = Array.from(container.querySelectorAll(".rounded-card"));
    expect(cardsAfter.some((card) => card.className.includes("bg-accent"))).toBe(false);
  });

  it("подсветка снимается по таймеру не короче длительности animate-glow (1.6s × 2 = 3.2s)", async () => {
    const user = userEvent.setup();
    const { container } = renderWithProviders(<HomeScreen />);
    await screen.findByText("2 из 3");

    const setTimeoutSpy = vi.spyOn(window, "setTimeout");

    await user.click(screen.getByRole("button", { name: /симулировать покупку/i }));

    await waitFor(() => {
      expect(container.querySelectorAll(".animate-glow")).toHaveLength(3);
    });

    const highlightTimer = setTimeoutSpy.mock.calls.find(
      ([, delay]) => typeof delay === "number" && delay >= 3200 && delay <= 4000,
    );
    expect(highlightTimer).toBeDefined();
    const [callback] = highlightTimer!;

    act(() => {
      (callback as () => void)();
    });

    expect(container.querySelectorAll(".animate-glow")).toHaveLength(0);

    setTimeoutSpy.mockRestore();
  });

  it("ошибка симуляции не показывает сырой error.message пользователю", async () => {
    server.use(http.post(`${API}/users/:user_id/receipts/simulate`, () => HttpResponse.error()));

    const user = userEvent.setup();
    renderWithProviders(<HomeScreen />);
    await screen.findByText("2 из 3");

    await user.click(screen.getByRole("button", { name: /симулировать покупку/i }));

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).not.toMatch(/failed to fetch/i);
  });
});
