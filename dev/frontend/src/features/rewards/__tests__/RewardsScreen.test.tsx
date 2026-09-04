import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { API } from "@/test/handlers";
import { server } from "@/test/setup";
import { renderWithProviders } from "@/test/render";
import { RewardsScreen } from "../RewardsScreen";

describe("RewardsScreen", () => {
  it("показывает баланс баллов одной цифрой, без разбивки по источникам", async () => {
    renderWithProviders(<RewardsScreen />);

    expect(await screen.findByText("480")).toBeInTheDocument();
    expect(screen.getByText("баллов")).toBeInTheDocument();
    expect(screen.queryByText("По чекам X5 Клуба")).not.toBeInTheDocument();
    expect(screen.queryByText("За цели и приглашения")).not.toBeInTheDocument();
  });

  it("показывает уровень и остаток опыта до следующего", async () => {
    renderWithProviders(<RewardsScreen />);

    expect(await screen.findByText("Уровень 7")).toBeInTheDocument();
    expect(screen.getByText("2 100 XP")).toBeInTheDocument();
    expect(screen.getByText("До уровня 8 осталось 700 XP")).toBeInTheDocument();
  });

  it("перечисляет правила начисления с числами из контракта", async () => {
    renderWithProviders(<RewardsScreen />);

    const receiptRule = await screen.findByText(
      "Чек засчитан: покупка в Пятёрочке или Перекрёстке",
    );
    expect(within(receiptRule.parentElement!).getByText("+10 XP")).toBeInTheDocument();
    expect(screen.getByText("+30…150 баллов")).toBeInTheDocument();
  });

  it("показывает историю начислений с объяснением каждой строки", async () => {
    renderWithProviders(<RewardsScreen />);

    expect(await screen.findByText("Покупка засчитана")).toBeInTheDocument();
    expect(screen.getByText("3 сентября · Молочный ритм")).toBeInTheDocument();
    expect(screen.getByText("2 сентября · Чек на 640 ₽")).toBeInTheDocument();
    expect(screen.getByText("+30 баллов")).toBeInTheDocument();
  });

  it("показывает подсказку про баллы при наведении и прячет при уходе курсора", async () => {
    const user = userEvent.setup();
    renderWithProviders(<RewardsScreen />);
    await screen.findByText("480");
    const hint = screen.getByRole("button", { name: "Откуда берутся баллы" });

    await user.hover(hint);
    expect(screen.getByRole("tooltip")).toHaveTextContent(/За обычную покупку баллов нет/);

    await user.unhover(hint);
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("даёт вернуться на главную, сохранив выбранного пользователя", async () => {
    renderWithProviders(<RewardsScreen />, ["/rewards?user=2"]);
    await screen.findByText("Уровень 4");

    expect(screen.getByRole("link", { name: "Вернуться на главную" })).toHaveAttribute(
      "href",
      "/?user=2",
    );
  });

  it("для пользователя без начислений показывает пустую историю", async () => {
    renderWithProviders(<RewardsScreen />, ["/rewards?user=3"]);

    expect(
      await screen.findByText("Пока ничего не начислено. Первая же покупка добавит опыт Домовому."),
    ).toBeInTheDocument();
  });

  it("показывает ошибку и даёт повторить запрос", async () => {
    server.use(
      http.get(`${API}/users/:user_id/rewards`, () => HttpResponse.json(null, { status: 500 })),
    );
    renderWithProviders(<RewardsScreen />);

    await waitFor(() => expect(screen.getByText("Не получилось загрузить")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "Повторить" })).toBeInTheDocument();
  });
});
