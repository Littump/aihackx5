import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { PmScreen } from "../PmScreen";
import { renderWithProviders } from "@/test/render";

describe("PmScreen", () => {
  it("рендерит блок Features с данными пользователя", async () => {
    renderWithProviders(<PmScreen />);
    expect(await screen.findByText("2/нед.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Features" })).toBeInTheDocument();
    expect(screen.getByText("600 ₽")).toBeInTheDocument();
    expect(screen.getByText("dairy")).toBeInTheDocument();
    expect(screen.getByText("32%")).toBeInTheDocument();
  });

  it("рендерит блок «Механика и почему»", async () => {
    renderWithProviders(<PmScreen />);
    expect(await screen.findByText("Челлендж")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Механика и почему" })).toBeInTheDocument();
    expect(screen.getByText("Нет выполненных челленджей на этой неделе")).toBeInTheDocument();
  });

  it("рендерит блок «Челлендж и экономика»", async () => {
    renderWithProviders(<PmScreen />);
    expect(await screen.findByText("3 покупки за неделю")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Челлендж и экономика" })).toBeInTheDocument();
    expect(screen.getByText("36 ₽")).toBeInTheDocument();
    expect(screen.getByText("890 XP + 620 баллов")).toBeInTheDocument();
    expect(screen.getByText(/360\s*₽/)).toBeInTheDocument();
  });

  it("рендерит блок Ledger", async () => {
    renderWithProviders(<PmScreen />);
    expect(await screen.findByText("receipt #501")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Ledger" })).toBeInTheDocument();
  });

  it("рендерит блок «Антифрод» со всеми решениями", async () => {
    renderWithProviders(<PmScreen />);
    expect(await screen.findByRole("heading", { name: "Антифрод" })).toBeInTheDocument();

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

  it("рендерит блок «Симуляция» с метриками и assumptions", async () => {
    renderWithProviders(<PmScreen />);
    expect(await screen.findByText(/27.?600\s*₽/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Симуляция" })).toBeInTheDocument();
    expect(screen.getByText(/simulation assumptions/)).toBeInTheDocument();
    expect(screen.getByText("users: 5000")).toBeInTheDocument();
  });

  it("рендерит блок Eval с метриками и таблицей профилей", async () => {
    renderWithProviders(<PmScreen />);
    expect(await screen.findByText("78%")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Eval" })).toBeInTheDocument();
    expect(screen.getByText("40 профилей")).toBeInTheDocument();
    expect(screen.getByText("profile_id")).toBeInTheDocument();
  });
});
