import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { PmScreen } from "../PmScreen";
import { renderWithProviders } from "@/test/render";

function cardOf(heading: HTMLElement): HTMLElement {
  const card = heading.closest(".rounded-card");
  if (card === null) throw new Error("не найдена карточка блока");
  return card as HTMLElement;
}

describe("PmScreen", () => {
  it("показывает плашку допущений симуляции один раз для всего экрана", async () => {
    renderWithProviders(<PmScreen />);
    await screen.findByRole("heading", { name: "Профиль и признаки" });
    expect(screen.getAllByText("Допущения симуляции, не фактические показатели X5.")).toHaveLength(
      1,
    );
  });

  it("рендерит блок «Профиль и признаки» с данными пользователя", async () => {
    renderWithProviders(<PmScreen />);
    expect(await screen.findByText("2/нед.")).toBeInTheDocument();
    const heading = screen.getByRole("heading", { name: "Профиль и признаки" });
    const card = within(cardOf(heading));
    expect(card.getByText("600 ₽")).toBeInTheDocument();
    expect(card.getByText("dairy")).toBeInTheDocument();
    expect(card.getByText("32%")).toBeInTheDocument();
  });

  it("рендерит блок «Механика и обоснование» с сырым значением enum", async () => {
    renderWithProviders(<PmScreen />);
    expect(await screen.findByText("challenge")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Механика и обоснование" })).toBeInTheDocument();
    expect(screen.getByText("Нет выполненных челленджей на этой неделе")).toBeInTheDocument();
  });

  it("рендерит блок «Экономика цели» с индикатором бюджета", async () => {
    renderWithProviders(<PmScreen />);
    expect(await screen.findByText("3 покупки за неделю")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Экономика цели" })).toBeInTheDocument();
    expect(screen.getByText("36 ₽")).toBeInTheDocument();
    expect(screen.getByText("890 XP + 620 баллов")).toBeInTheDocument();
    expect(screen.getByText(/360\s*₽/)).toBeInTheDocument();
    expect(screen.getByText(/Награда укладывается в бюджет: 30 из 36 ₽/)).toBeInTheDocument();
  });

  it("рендерит блок «Журнал начислений»", async () => {
    renderWithProviders(<PmScreen />);
    const heading = await screen.findByRole("heading", { name: "Журнал начислений" });
    expect(within(cardOf(heading)).getByText("receipt #501")).toBeInTheDocument();
  });

  it("рендерит блок «Антифрод» пользователя из fraud_checks в PmUserResponse", async () => {
    renderWithProviders(<PmScreen />);
    expect(await screen.findByRole("heading", { name: "Антифрод" })).toBeInTheDocument();
    expect(await screen.findByTestId("user-fraud-score")).toHaveTextContent("0.10");
    expect(screen.getByTestId("user-fraud-decision-badge")).toHaveTextContent("Одобрено");
  });

  it("рендерит блок «Все проверки антифрода» со всеми решениями", async () => {
    renderWithProviders(<PmScreen />);
    expect(
      await screen.findByRole("heading", { name: "Все проверки антифрода" }),
    ).toBeInTheDocument();

    const badges = await screen.findAllByTestId("fraud-decision-badge");
    const decisions = badges.map((badge) => badge.textContent);
    expect(decisions).toEqual(expect.arrayContaining(["Одобрено", "Отложено", "Заблокировано"]));
    expect(screen.getByText(/4x частота за неделю/)).toBeInTheDocument();
  });

  it("фильтр антифрода по decision меняет видимые записи", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PmScreen />);
    await screen.findAllByTestId("fraud-decision-badge");

    await user.selectOptions(screen.getByLabelText("Фильтр по решению"), "block");

    await waitFor(() => {
      const decisions = screen
        .getAllByTestId("fraud-decision-badge")
        .map((badge) => badge.textContent);
      expect(decisions).toEqual(["Заблокировано"]);
    });
  });

  it("рендерит блок «Симуляция: контроль и тест» с таблицей и метриками", async () => {
    renderWithProviders(<PmScreen />);
    expect(await screen.findByText(/27.?600\s*₽/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Симуляция: контроль и тест" })).toBeInTheDocument();
    expect(screen.getByText("4.50")).toBeInTheDocument();
    expect(screen.getByText("users: 5000")).toBeInTheDocument();
  });

  it("рендерит блок «Качество подбора целей ИИ» с плитками и таблицей профилей", async () => {
    renderWithProviders(<PmScreen />);
    expect(await screen.findByText("78%")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Качество подбора целей ИИ" })).toBeInTheDocument();
    expect(screen.getByText("40")).toBeInTheDocument();
    expect(screen.getByText("profile_id")).toBeInTheDocument();
  });

  it("держит карточки в одну колонку по умолчанию и в две — от md, EvalBlock растянут на всю ширину", async () => {
    const { container } = renderWithProviders(<PmScreen />);
    await screen.findByRole("heading", { name: "Профиль и признаки" });

    const grid = container.querySelector(".grid-cols-1");
    expect(grid).not.toBeNull();
    expect(grid).toHaveClass("grid", "grid-cols-1", "md:grid-cols-2");

    const evalHeading = screen.getByRole("heading", { name: "Качество подбора целей ИИ" });
    const evalCard = evalHeading.closest(".rounded-card");
    expect(evalCard?.parentElement).toHaveClass("md:col-span-2");

    const allChecksHeading = screen.getByRole("heading", { name: "Все проверки антифрода" });
    expect(allChecksHeading.closest(".rounded-card")?.closest(".grid-cols-1")).toBeNull();
  });
});
