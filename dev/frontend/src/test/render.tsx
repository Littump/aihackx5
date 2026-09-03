import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router";
import { UserProvider } from "@/features/users/UserContext";

export function renderWithProviders(
  ui: ReactElement,
  initialEntries: string[] = ["/?user=1"],
  client: QueryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } }),
) {
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={initialEntries}>
        <UserProvider>{ui}</UserProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}
