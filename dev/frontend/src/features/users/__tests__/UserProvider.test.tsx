import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Link, MemoryRouter, useSearchParams } from "react-router";
import { describe, expect, it } from "vitest";
import { UserProvider } from "../UserContext";
import { useUserContext } from "../hooks";

function CurrentUserProbe() {
  const [params] = useSearchParams();
  const { userId } = useUserContext();
  return (
    <>
      <span data-testid="search">{params.toString()}</span>
      <span data-testid="user-id">{userId ?? "нет"}</span>
    </>
  );
}

function renderWithLinkWithoutParams(initialEntries: string[]) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={initialEntries}>
        <UserProvider>
          <Link to="/league">Лига</Link>
          <CurrentUserProbe />
        </UserProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("UserProvider — выбранный пользователь переживает переход между экранами", () => {
  it("возвращает выбранного пользователя в URL, если ссылка потеряла ?user=", async () => {
    const user = userEvent.setup();
    renderWithLinkWithoutParams(["/?user=2"]);
    await waitFor(() => expect(screen.getByTestId("user-id")).toHaveTextContent("2"));

    await user.click(screen.getByRole("link", { name: "Лига" }));

    await waitFor(() => expect(screen.getByTestId("search")).toHaveTextContent("user=2"));
    expect(screen.getByTestId("user-id")).toHaveTextContent("2");
  });

  it("не подменяет выбранного пользователя первым из списка", async () => {
    const user = userEvent.setup();
    renderWithLinkWithoutParams(["/?user=3"]);
    await waitFor(() => expect(screen.getByTestId("user-id")).toHaveTextContent("3"));

    await user.click(screen.getByRole("link", { name: "Лига" }));

    await waitFor(() => expect(screen.getByTestId("search")).toHaveTextContent("user=3"));
  });

  it("при заходе без параметра берёт первого пользователя из списка", async () => {
    renderWithLinkWithoutParams(["/"]);

    await waitFor(() => expect(screen.getByTestId("search")).toHaveTextContent("user=1"));
  });
});
