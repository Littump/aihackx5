import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { HomeScreen } from "../HomeScreen";
import { API } from "@/test/handlers";
import { buildReceiptProcessingResult, getSimulateDraft } from "@/test/fixtures";
import { renderWithProviders } from "@/test/render";
import { server } from "@/test/setup";

type SimulatePayload = { items: { category: string; price: number; is_promo: boolean }[] };

const DAIRY_GOAL_DRAFT = {
  ...getSimulateDraft(1),
  goal: {
    type: "category" as const,
    category: "dairy",
    title: "2 покупки молочки",
    progress: 1,
    target: 2,
  },
  items: [
    {
      product_name: "Молочный товар 1",
      category: "dairy",
      price: 120,
      is_promo: false,
      matches_goal: true,
    },
    {
      product_name: "Хлебный товар 2",
      category: "bakery",
      price: 80,
      is_promo: false,
      matches_goal: false,
    },
  ],
};

async function openReceipt(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole("button", { name: /симулировать покупку/i }));
  return await screen.findByRole("dialog", { name: "Чек покупки" });
}

describe("ReceiptSheet", () => {
  it("по клику «Симулировать покупку» показывает чек с позициями из черновика", async () => {
    const user = userEvent.setup();
    renderWithProviders(<HomeScreen />);
    await screen.findByText("2 из 3");

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();

    const dialog = await openReceipt(user);

    expect(within(dialog).getByText("Пятёрочка на Ленина")).toBeInTheDocument();
    expect(within(dialog).getAllByRole("listitem")).toHaveLength(3);
    expect(within(dialog).getByTestId("receipt-total")).toHaveTextContent("350 ₽");
  });

  it("удаление позиции уменьшает итог и не отправляет её на backend", async () => {
    const user = userEvent.setup();
    let payload: SimulatePayload | null = null;
    server.use(
      http.post(`${API}/users/:user_id/receipts/simulate`, async ({ request }) => {
        payload = (await request.json()) as SimulatePayload;
        return HttpResponse.json(buildReceiptProcessingResult(1), { status: 201 });
      }),
    );

    renderWithProviders(<HomeScreen />);
    await screen.findByText("2 из 3");
    const dialog = await openReceipt(user);

    await user.click(within(dialog).getByRole("button", { name: "Удалить: Хлебный товар 2" }));

    expect(within(dialog).getAllByRole("listitem")).toHaveLength(2);
    expect(within(dialog).getByTestId("receipt-total")).toHaveTextContent("270 ₽");

    await user.click(within(dialog).getByRole("button", { name: "Подтвердить покупку" }));

    await waitFor(() => expect(payload).not.toBeNull());
    expect(payload!.items.map((item) => item.category)).toEqual(["dairy", "fruits_veg"]);
  });

  it("добавленный товар попадает в чек и в запрос", async () => {
    const user = userEvent.setup();
    let payload: SimulatePayload | null = null;
    server.use(
      http.post(`${API}/users/:user_id/receipts/simulate`, async ({ request }) => {
        payload = (await request.json()) as SimulatePayload;
        return HttpResponse.json(buildReceiptProcessingResult(1), { status: 201 });
      }),
    );

    renderWithProviders(<HomeScreen />);
    await screen.findByText("2 из 3");
    const dialog = await openReceipt(user);

    await user.selectOptions(within(dialog).getByRole("combobox"), "meat_fish");
    await user.click(within(dialog).getByRole("checkbox", { name: /по акции/i }));
    await user.click(within(dialog).getByRole("button", { name: "Добавить в чек" }));

    expect(within(dialog).getAllByRole("listitem")).toHaveLength(4);
    expect(within(dialog).getByTestId("receipt-total")).toHaveTextContent("500 ₽");

    await user.click(within(dialog).getByRole("button", { name: "Подтвердить покупку" }));

    await waitFor(() => expect(payload).not.toBeNull());
    expect(payload!.items).toHaveLength(4);
    expect(payload!.items[3]).toMatchObject({
      category: "meat_fish",
      price: 150,
      is_promo: true,
    });
  });

  it("подсказка цели меняется, когда из чека убрали категорию цели недели", async () => {
    const user = userEvent.setup();
    server.use(
      http.get(`${API}/users/:user_id/receipts/simulate/draft`, () =>
        HttpResponse.json(DAIRY_GOAL_DRAFT),
      ),
    );

    renderWithProviders(<HomeScreen />);
    await screen.findByText("2 из 3");
    const dialog = await openReceipt(user);

    expect(within(dialog).getByText(/цель сдвинется/i)).toBeInTheDocument();
    expect(within(dialog).getAllByText("к цели")).toHaveLength(1);

    await user.click(within(dialog).getByRole("button", { name: "Удалить: Молочный товар 1" }));

    expect(within(dialog).getByText(/цель не сдвинется/i)).toBeInTheDocument();
  });

  it("пустой чек нельзя подтвердить", async () => {
    const user = userEvent.setup();
    server.use(
      http.get(`${API}/users/:user_id/receipts/simulate/draft`, () =>
        HttpResponse.json(DAIRY_GOAL_DRAFT),
      ),
    );

    renderWithProviders(<HomeScreen />);
    await screen.findByText("2 из 3");
    const dialog = await openReceipt(user);

    await user.click(within(dialog).getByRole("button", { name: "Удалить: Молочный товар 1" }));
    await user.click(within(dialog).getByRole("button", { name: "Удалить: Хлебный товар 2" }));

    expect(within(dialog).getByRole("button", { name: "Подтвердить покупку" })).toBeDisabled();
    expect(within(dialog).getByText(/чек пустой/i)).toBeInTheDocument();
  });

  it("«Отмена» закрывает чек без запроса на backend", async () => {
    const user = userEvent.setup();
    let simulateCalled = false;
    server.use(
      http.post(`${API}/users/:user_id/receipts/simulate`, () => {
        simulateCalled = true;
        return HttpResponse.json(buildReceiptProcessingResult(1), { status: 201 });
      }),
    );

    renderWithProviders(<HomeScreen />);
    await screen.findByText("2 из 3");
    const dialog = await openReceipt(user);

    await user.click(within(dialog).getByRole("button", { name: "Отмена" }));

    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(simulateCalled).toBe(false);
  });

  it("ошибка загрузки черновика показывает понятный текст и кнопку повтора", async () => {
    const user = userEvent.setup();
    server.use(
      http.get(`${API}/users/:user_id/receipts/simulate/draft`, () => HttpResponse.error()),
    );

    renderWithProviders(<HomeScreen />);
    await screen.findByText("2 из 3");
    const dialog = await openReceipt(user);

    const alert = await within(dialog).findByRole("alert");
    expect(alert.textContent).toMatch(/не получилось собрать чек/i);
    expect(alert.textContent).not.toMatch(/failed to fetch/i);
    expect(within(dialog).getByRole("button", { name: "Повторить" })).toBeInTheDocument();
  });
});
