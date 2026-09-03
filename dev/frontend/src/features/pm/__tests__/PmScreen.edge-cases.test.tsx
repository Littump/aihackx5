import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { PmScreen } from "../PmScreen";
import { API } from "@/test/handlers";
import { getPmUser } from "@/test/fixtures";
import { renderWithProviders } from "@/test/render";
import { server } from "@/test/setup";

function serverError(message: string) {
  return () => HttpResponse.json({ error: { code: "internal_error", message } }, { status: 500 });
}

describe("PmScreen — состояния загрузки и ошибок", () => {
  it("показывает статус загрузки, пока PM-карточка ещё не пришла", () => {
    renderWithProviders(<PmScreen />);
    expect(screen.getByText("Загрузка данных пользователя…")).toBeInTheDocument();
  });

  it("показывает ошибку, если PM-карточка не загрузилась", async () => {
    server.use(http.get(`${API}/pm/users/:user_id`, serverError("БД недоступна")));

    renderWithProviders(<PmScreen />);

    expect(await screen.findByText(/Не удалось загрузить PM-карточку/)).toBeInTheDocument();
    expect(screen.getByText(/БД недоступна/)).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Features" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Симуляция" })).not.toBeInTheDocument();
  });

  it("показывает ошибку антифрода, если /pm/fraud недоступен", async () => {
    server.use(http.get(`${API}/pm/fraud`, serverError("timeout")));

    renderWithProviders(<PmScreen />);

    expect(await screen.findByText(/Не удалось загрузить проверки/)).toBeInTheDocument();
  });

  it("показывает ошибку симуляции, если сбой отличается от 404", async () => {
    server.use(http.get(`${API}/pm/simulation/latest`, serverError("timeout")));

    renderWithProviders(<PmScreen />);

    expect(await screen.findByText(/Не удалось загрузить симуляцию/)).toBeInTheDocument();
    expect(screen.queryByText("Ещё не запускали.")).not.toBeInTheDocument();
  });

  it("показывает ошибку eval, если сбой отличается от 404", async () => {
    server.use(http.get(`${API}/pm/eval/latest`, serverError("timeout")));

    renderWithProviders(<PmScreen />);

    expect(await screen.findByText(/Не удалось загрузить eval/)).toBeInTheDocument();
  });
});

describe("PmScreen — граничные состояния данных", () => {
  it("показывает заглушку, если у пользователя нет активного hero-челленджа", async () => {
    renderWithProviders(<PmScreen />, ["/?user=3"]);

    expect(await screen.findByText("Активного hero-челленджа нет.")).toBeInTheDocument();
    expect(screen.queryByText("Baseline")).not.toBeInTheDocument();
  });

  it("не рендерит таблицу категорий, если affinity пуст", async () => {
    renderWithProviders(<PmScreen />, ["/?user=3"]);

    await screen.findByRole("heading", { name: "Features" });
    expect(screen.queryByText("Категории")).not.toBeInTheDocument();
  });

  it("показывает «Записей пока нет.» для пустого ledger", async () => {
    server.use(
      http.get(`${API}/pm/users/:user_id`, () =>
        HttpResponse.json({ ...getPmUser(1), ledger: [] }),
      ),
    );

    renderWithProviders(<PmScreen />);

    expect(await screen.findByText("Записей пока нет.")).toBeInTheDocument();
  });

  it("показывает «Проверок нет.», если список антифрода пуст", async () => {
    server.use(http.get(`${API}/pm/fraud`, () => HttpResponse.json({ items: [] })));

    renderWithProviders(<PmScreen />);

    await screen.findByRole("heading", { name: "Антифрод" });
    expect(await screen.findByText("Проверок нет.")).toBeInTheDocument();
  });
});
