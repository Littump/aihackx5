import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import { UserProvider } from "@/features/users/UserContext";
import { API } from "@/test/handlers";
import { heroChallenge, sideChallenges } from "@/test/fixtures/challenges";
import { server } from "@/test/setup";
import { ChallengeScreen } from "../ChallengeScreen";

function renderScreen(initialEntry = "/challenge?user=1") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <UserProvider>
          <ChallengeScreen />
        </UserProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("ChallengeScreen", () => {
  it("показывает hero, side и историю выполненных челленджей", async () => {
    renderScreen();

    expect(await screen.findByRole("heading", { name: "3 покупки за неделю" })).toBeInTheDocument();
    expect(screen.getByText("2 покупки молочки за неделю")).toBeInTheDocument();
    expect(screen.getByText("2 из 3")).toBeInTheDocument();
    expect(screen.getByText("+50 XP и 30 баллов")).toBeInTheDocument();
    expect(screen.getAllByText("+50 XP · 30 баллов").length).toBeGreaterThan(0);
    expect(screen.getByText("30 августа · выполнено")).toBeInTheDocument();
  });

  it("объяснение в hero-карточке видно сразу, без клика", async () => {
    renderScreen();

    await screen.findByRole("heading", { name: "3 покупки за неделю" });
    expect(
      screen.getByText("Обычно 2 покупки в неделю (baseline 2), цель — 3 до конца недели."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Почему это мне?" })).not.toBeInTheDocument();
  });

  it("side-карточка показывает реальный прогресс и без кнопки «Взять цель»", async () => {
    renderScreen();

    const sideTitle = await screen.findByText("2 покупки молочки за неделю");
    const sideCard = sideTitle.closest("section");
    if (sideCard === null) throw new Error("side card not found");

    expect(within(sideCard).getByText("1 из 2")).toBeInTheDocument();
    expect(within(sideCard).getByText("до 6 сентября")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Взять цель" })).not.toBeInTheDocument();
  });

  it("показывает пустое состояние и обновляет челленджи по клику", async () => {
    let refreshed = false;
    server.use(
      http.get(`${API}/users/:user_id/challenges`, () =>
        HttpResponse.json(
          refreshed
            ? { hero: heroChallenge(1), side: [], history: [] }
            : { hero: null, side: [], history: [] },
        ),
      ),
      http.post(`${API}/users/:user_id/challenges/refresh`, () => {
        refreshed = true;
        return HttpResponse.json({ hero: heroChallenge(1), side: [], history: [] });
      }),
    );

    const user = userEvent.setup();
    renderScreen("/challenge?user=3");

    expect(await screen.findByText("Домовой думает над целью недели…")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Обновить" }));

    expect(await screen.findByText("3 покупки за неделю")).toBeInTheDocument();
    expect(screen.queryByText("Домовой думает над целью недели…")).not.toBeInTheDocument();
  });

  it("показывает реальный тип и baseline/target в плитках hero-карточки", async () => {
    renderScreen();
    const heroHeading = await screen.findByRole("heading", { name: "3 покупки за неделю" });
    const heroCard = heroHeading.closest("section");
    if (heroCard === null) throw new Error("hero card not found");

    expect(within(heroCard).getByText("Частота покупок")).toBeInTheDocument();
    expect(
      within(heroCard).getByText("Обычно у вас 2 покупки в неделю. Сделайте 3 до воскресенья."),
    ).toBeInTheDocument();
    expect(within(heroCard).getByText("Ваша обычная норма")).toBeInTheDocument();
    expect(within(heroCard).getByText("2")).toBeInTheDocument();
    expect(within(heroCard).getByText("Цель")).toBeInTheDocument();
    expect(within(heroCard).getByText("3")).toBeInTheDocument();
  });

  it("показывает ошибку, если список челленджей не загрузился", async () => {
    server.use(
      http.get(`${API}/users/:user_id/challenges`, () =>
        HttpResponse.json(
          { error: { code: "down", message: "домовой недоступен" } },
          { status: 500 },
        ),
      ),
    );

    renderScreen();

    expect(
      await screen.findByText(/Не удалось загрузить челленджи: домовой недоступен/),
    ).toBeInTheDocument();
  });

  it("если hero отсутствует, но есть side-челленджи, пустое состояние не показывается", async () => {
    server.use(
      http.get(`${API}/users/:user_id/challenges`, () =>
        HttpResponse.json({ hero: null, side: sideChallenges(1), history: [] }),
      ),
    );

    renderScreen();

    expect(await screen.findByText("2 покупки молочки за неделю")).toBeInTheDocument();
    expect(screen.queryByText("Домовой думает над целью недели…")).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "3 покупки за неделю" })).not.toBeInTheDocument();
  });

  it("прогресс, равный target, отображается без переполнения", async () => {
    const completedHero = { ...heroChallenge(1)!, progress: 3 };
    server.use(
      http.get(`${API}/users/:user_id/challenges`, () =>
        HttpResponse.json({ hero: completedHero, side: [], history: [] }),
      ),
    );

    renderScreen();

    await screen.findByRole("heading", { name: "3 покупки за неделю" });
    const progress = screen.getByRole("progressbar");
    expect(progress).toHaveAttribute("aria-valuenow", "3");
    expect(progress).toHaveAttribute("aria-valuemax", "3");
    expect(screen.getByText("3 из 3")).toBeInTheDocument();
  });

  it("показывает плейсхолдер истории, если завершённых челленджей ещё нет", async () => {
    renderScreen("/challenge?user=2");

    await screen.findByRole("heading", { name: "3 покупки за неделю" });
    expect(screen.getByText("Пока нет выполненных челленджей.")).toBeInTheDocument();
  });
});
