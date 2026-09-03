import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ChallengeHistoryItem } from "../api";
import { ChallengeHistoryList } from "../components/ChallengeHistoryList";

function historyItem(overrides: Partial<ChallengeHistoryItem>): ChallengeHistoryItem {
  return {
    id: 1,
    type: "frequency",
    category: null,
    status: "completed",
    is_hero: true,
    baseline: 2,
    target: 3,
    progress: 3,
    period_start: "2026-08-24T00:00:00+03:00",
    period_end: "2026-08-30T23:59:59+03:00",
    reward_xp: 50,
    reward_points: 30,
    title: "3 покупки за неделю",
    body: "Обычно у вас 2 покупки в неделю. Сделайте 3 до воскресенья.",
    ...overrides,
  };
}

const STATUS_CASES: {
  status: ChallengeHistoryItem["status"];
  text: string;
  hasReward: boolean;
}[] = [
  { status: "completed", text: "выполнено", hasReward: true },
  { status: "failed", text: "не успели", hasReward: false },
  { status: "expired", text: "истекло", hasReward: false },
];

describe("ChallengeHistoryList", () => {
  it.each(STATUS_CASES)(
    "статус $status передаётся текстом «$text» рядом с иконкой",
    ({ status, text, hasReward }) => {
      render(<ChallengeHistoryList items={[historyItem({ status })]} />);

      expect(screen.getByText(new RegExp(text))).toBeInTheDocument();
      expect(
        screen.getByText(hasReward ? "+50 XP · 30 баллов" : "без награды"),
      ).toBeInTheDocument();
    },
  );

  it("у трёх статусов истории — три разных SVG-иконки, не одна и та же с другим цветом", () => {
    const items = STATUS_CASES.map((c, index) => historyItem({ id: index + 1, status: c.status }));
    const { container } = render(<ChallengeHistoryList items={items} />);

    const iconPaths = Array.from(container.querySelectorAll("svg")).map((svg) => svg.innerHTML);
    expect(new Set(iconPaths).size).toBe(iconPaths.length);
  });

  it("неизвестный статус active не роняет компонент и получает нейтральный вид", () => {
    render(<ChallengeHistoryList items={[historyItem({ status: "active" })]} />);

    expect(screen.getByText(/активно/)).toBeInTheDocument();
  });

  it("пустая история показывает плейсхолдер без секции-списка", () => {
    render(<ChallengeHistoryList items={[]} />);

    expect(screen.getByText("Пока нет выполненных челленджей.")).toBeInTheDocument();
  });
});
