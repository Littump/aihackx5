import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it } from "vitest";
import { routes } from "../router";

function renderApp(initialEntries: string[]) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createMemoryRouter(routes, { initialEntries });
  const view = render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return { router, ...view };
}

describe("router", () => {
  it.each(["/", "/challenge", "/league", "/referral", "/pm"])(
    "рендерит маршрут %s с моками",
    async (path) => {
      renderApp([`${path}?user=1`]);
      await waitFor(() => {
        expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
      });
    },
  );

  it("нижняя навигация не содержит пункта PM", async () => {
    renderApp(["/?user=1"]);
    await waitFor(() => screen.getByRole("heading", { level: 1 }));
    expect(screen.queryByRole("link", { name: /pm/i })).not.toBeInTheDocument();
  });

  it("нижняя навигация рендерится на consumer-роутах, но не на /pm", async () => {
    const home = renderApp(["/?user=1"]);
    await waitFor(() => screen.getByRole("heading", { level: 1 }));
    expect(screen.getByRole("navigation", { name: "Основная навигация" })).toBeInTheDocument();
    home.unmount();

    renderApp(["/pm?user=1"]);
    await waitFor(() => screen.getByRole("heading", { level: 1 }));
    expect(
      screen.queryByRole("navigation", { name: "Основная навигация" }),
    ).not.toBeInTheDocument();
  });
});
