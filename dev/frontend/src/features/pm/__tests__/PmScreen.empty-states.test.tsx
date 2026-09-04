import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { PmScreen } from "../PmScreen";
import { API } from "@/test/handlers";
import { renderWithProviders } from "@/test/render";
import { server } from "@/test/setup";

function notFound() {
  return HttpResponse.json(
    { error: { code: "not_found", message: "Пока нет данных" } },
    {
      status: 404,
    },
  );
}

describe("PmScreen — пустые состояния", () => {
  it("показывает «ещё не запускали» вместо симуляции при 404", async () => {
    server.use(http.get(`${API}/pm/simulation/latest`, notFound));

    renderWithProviders(<PmScreen />);

    await screen.findByRole("heading", { name: "Симуляция: контроль и тест" });
    expect(await screen.findByText("Ещё не запускали.")).toBeInTheDocument();
  });

  it("показывает «ещё не запускали» вместо eval при 404", async () => {
    server.use(http.get(`${API}/pm/eval/latest`, notFound));

    renderWithProviders(<PmScreen />);

    await screen.findByRole("heading", { name: "Качество подбора целей ИИ" });
    expect(await screen.findByText("Ещё не запускали.")).toBeInTheDocument();
  });

  it("показывает «ещё не запускали» для обоих блоков одновременно", async () => {
    server.use(
      http.get(`${API}/pm/simulation/latest`, notFound),
      http.get(`${API}/pm/eval/latest`, notFound),
    );

    renderWithProviders(<PmScreen />);

    await waitFor(() => {
      expect(screen.getAllByText("Ещё не запускали.")).toHaveLength(2);
    });
  });
});
