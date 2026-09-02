import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { delay, http, HttpResponse } from "msw";
import { MemoryRouter, useSearchParams } from "react-router";
import { describe, expect, it } from "vitest";
import { API } from "@/test/handlers";
import { server } from "@/test/setup";
import { UserProvider } from "../UserContext";
import { UserSwitcher } from "../UserSwitcher";

function SearchParamsProbe() {
  const [params] = useSearchParams();
  return <span data-testid="search">{params.toString()}</span>;
}

function renderSwitcher() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/"]}>
        <UserProvider>
          <UserSwitcher />
          <SearchParamsProbe />
        </UserProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("UserSwitcher", () => {
  it("подставляет первого пользователя в ?user= по умолчанию", async () => {
    renderSwitcher();
    await waitFor(() => expect(screen.getByTestId("search")).toHaveTextContent("user=1"));
  });

  it("смена пользователя в селекте меняет ?user= в URL", async () => {
    const user = userEvent.setup();
    renderSwitcher();

    const select = await screen.findByLabelText("Переключить пользователя");
    await waitFor(() => expect(screen.getByTestId("search")).toHaveTextContent("user=1"));

    await user.selectOptions(select, "2");

    await waitFor(() => expect(screen.getByTestId("search")).toHaveTextContent("user=2"));
  });

  it("пока список пользователей не загружен, селект заблокирован и показывает плейсхолдер", async () => {
    server.use(
      http.get(`${API}/users`, async () => {
        await delay(50);
        return HttpResponse.json({ items: [] });
      }),
    );

    renderSwitcher();

    const select = screen.getByLabelText("Переключить пользователя");
    expect(select).toBeDisabled();
    expect(screen.getByText("Загрузка…")).toBeInTheDocument();
  });
});
