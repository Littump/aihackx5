import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it } from "vitest";
import { PmLayout } from "@/app/PmLayout";

function renderPmLayout() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createMemoryRouter(
    [
      {
        path: "/pm",
        element: <PmLayout />,
        children: [{ index: true, element: <div data-testid="pm-content">Контент PM</div> }],
      },
    ],
    { initialEntries: ["/pm?user=1"] },
  );
  return render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

describe("PmLayout", () => {
  it("ограничивает контент до 960px и центрирует его", async () => {
    renderPmLayout();
    const content = await screen.findByTestId("pm-content");
    const section = content.closest("section");
    expect(section).toHaveClass("max-w-pm", "mx-auto");
  });

  it("не осталось старого фиксированного max-w-6xl", async () => {
    const { container } = renderPmLayout();
    await screen.findByTestId("pm-content");
    expect(container.querySelector(".max-w-6xl")).toBeNull();
  });

  it("оборачивает контент в rounded-sheet карточку на фоне bg-desk", async () => {
    const { container } = renderPmLayout();
    const content = await screen.findByTestId("pm-content");

    const card = content.parentElement;
    expect(card).toHaveClass("rounded-sheet", "bg-canvas", "shadow-lift");

    const outer = container.firstElementChild;
    expect(outer).toHaveClass("bg-desk");
  });

  it("демо-полоса переключения пользователя рендерится вне карточки контента", async () => {
    renderPmLayout();
    await screen.findByTestId("pm-content");

    const select = await screen.findByLabelText("Переключить пользователя");
    const card = screen.getByTestId("pm-content").parentElement;
    expect(card?.contains(select)).toBe(false);
  });
});
