import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { HomeScreen } from "../HomeScreen";
import { API } from "@/test/handlers";
import { renderWithProviders } from "@/test/render";
import { server } from "@/test/setup";

describe("HomeScreen", () => {
  it("показывает статус backend", async () => {
    renderWithProviders(<HomeScreen />);
    expect(await screen.findByText("Backend: ok, база: ok")).toBeInTheDocument();
  });

  it("показывает ошибку, если backend недоступен", async () => {
    server.use(
      http.get(`${API}/health`, () =>
        HttpResponse.json({ error: { code: "down", message: "нет базы" } }, { status: 500 }),
      ),
    );
    renderWithProviders(<HomeScreen />);
    expect(await screen.findByText(/Backend недоступен/)).toBeInTheDocument();
  });
});
