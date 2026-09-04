import { formatCategoryLabel } from "../categoryLabels";
import type { SimulateDraft } from "../api";

type GoalHintProps = {
  goal: SimulateDraft["goal"];
  goalLines: number;
};

export function GoalHint({ goal, goalLines }: GoalHintProps) {
  if (goal === null) {
    return (
      <p className="rounded-tile bg-canvas p-3 text-caption text-ink-500">
        Цели недели пока нет — чек всё равно даст XP и копилку.
      </p>
    );
  }

  if (goal.type === "frequency" || goal.category === null) {
    return (
      <p className="rounded-tile bg-brand-50 p-3 text-caption text-brand-700">
        Цель недели: {goal.title} — {goal.progress} из {goal.target}. Засчитывается любой чек.
      </p>
    );
  }

  const label = formatCategoryLabel(goal.category);
  const tone = goalLines > 0 ? "bg-brand-50 text-brand-700" : "bg-accent-50 text-accent-700";
  const status =
    goalLines > 0
      ? `В чеке есть «${label}» — цель сдвинется.`
      : `В чеке нет «${label}» — цель не сдвинется.`;

  return (
    <p className={`rounded-tile p-3 text-caption ${tone}`}>
      Цель недели: {goal.title} — {goal.progress} из {goal.target}. {status}
    </p>
  );
}
