import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { UserFraudBlock } from "../components/UserFraudBlock";
import type { FraudCheck } from "../api";

function buildCheck(overrides: Partial<FraudCheck> = {}): FraudCheck {
  return {
    id: 1,
    subject_type: "receipt",
    subject_id: 1,
    user_id: 1,
    score: 0.3,
    decision: "approve",
    signals: [],
    created_at: "2026-08-01T10:00:00+03:00",
    ...overrides,
  };
}

describe("UserFraudBlock — пустое состояние", () => {
  it("показывает нейтральное сообщение, если проверок ещё не было", () => {
    render(<UserFraudBlock fraudChecks={[]} />);
    expect(screen.getByText("Проверок пока не было.")).toBeInTheDocument();
    expect(screen.queryByTestId("fraud-gauge-fill")).not.toBeInTheDocument();
  });
});

describe("UserFraudBlock — берёт последнюю проверку по created_at", () => {
  it("рендерит именно последнюю запись, а не первую в массиве", () => {
    const older = buildCheck({
      id: 1,
      score: 0.1,
      decision: "approve",
      created_at: "2026-08-01T10:00:00+03:00",
    });
    const latest = buildCheck({
      id: 2,
      score: 0.62,
      decision: "hold",
      created_at: "2026-09-01T14:00:00+03:00",
      signals: [
        {
          code: "frequency_spike",
          weight: 0.28,
          strong: true,
          detail: "Несколько чеков за 10 минут",
        },
        { code: "device_new", weight: 0.09, strong: false, detail: "Новое устройство" },
      ],
    });

    render(<UserFraudBlock fraudChecks={[older, latest]} />);

    expect(screen.getByTestId("user-fraud-score")).toHaveTextContent("0.62");
    expect(screen.getByTestId("user-fraud-decision-badge")).toHaveTextContent("Отложено");
    expect(screen.getByText(/Несколько чеков за 10 минут/)).toBeInTheDocument();
    expect(screen.getByText("сильный")).toBeInTheDocument();
    expect(screen.getByText("слабый")).toBeInTheDocument();
  });
});

describe("UserFraudBlock — шкала антифрода", () => {
  it("ставит засечки ровно на порогах 0.5 и 0.8 и заливает шкалу по score", () => {
    render(<UserFraudBlock fraudChecks={[buildCheck({ score: 0.62 })]} />);

    expect(screen.getByTestId("fraud-gauge-tick-hold")).toHaveStyle({ width: "50%" });
    expect(screen.getByTestId("fraud-gauge-tick-block")).toHaveStyle({ width: "80%" });
    expect(screen.getByTestId("fraud-gauge-fill")).toHaveStyle({ width: "62%" });
    expect(screen.getByText("текущий 0.62")).toBeInTheDocument();
  });

  it("не выходит за пределы шкалы для score вне 0..1", () => {
    render(<UserFraudBlock fraudChecks={[buildCheck({ score: 1.4 })]} />);

    expect(screen.getByTestId("fraud-gauge-fill")).toHaveStyle({ width: "100%" });
  });
});
