import { useState, type ChangeEvent } from "react";
import { Card } from "@/shared/ui/Card";
import { usePmFraudChecks } from "../hooks";
import { decisionBadgeClass, decisionLabel, formatDateTime } from "../format";
import type { FraudCheck, FraudDecision } from "../api";

const DECISION_OPTIONS: Array<{ value: FraudDecision | ""; label: string }> = [
  { value: "", label: "Все решения" },
  { value: "approve", label: decisionLabel("approve") },
  { value: "hold", label: decisionLabel("hold") },
  { value: "block", label: decisionLabel("block") },
];

export function FraudBlock() {
  const [decision, setDecision] = useState<FraudDecision | null>(null);
  const fraudQuery = usePmFraudChecks(decision);

  function handleChange(event: ChangeEvent<HTMLSelectElement>) {
    const value = event.target.value as FraudDecision | "";
    setDecision(value === "" ? null : value);
  }

  return (
    <Card className="flex w-full flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lead font-bold">Все проверки антифрода</h2>
        <select
          aria-label="Фильтр по решению"
          value={decision ?? ""}
          onChange={handleChange}
          className="rounded-tile border border-line bg-surface px-2 py-1 text-body text-ink-900"
        >
          {DECISION_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {fraudQuery.isPending && <p className="text-ink-500">Загрузка…</p>}
      {fraudQuery.isError && (
        <p className="text-accent-700">Не удалось загрузить проверки: {fraudQuery.error.message}</p>
      )}
      {fraudQuery.data && <FraudTable items={fraudQuery.data.items} />}
    </Card>
  );
}

function FraudTable({ items }: { items: FraudCheck[] }) {
  if (items.length === 0) return <p className="text-ink-500">Проверок нет.</p>;

  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full min-w-[640px] border-collapse text-body">
        <thead>
          <tr className="text-left text-caption text-ink-500">
            <th className="py-2 font-normal">Когда</th>
            <th className="py-2 font-normal">Пользователь</th>
            <th className="py-2 font-normal">Объект</th>
            <th className="py-2 font-normal">Оценка</th>
            <th className="py-2 font-normal">Решение</th>
            <th className="py-2 font-normal">Сигналы</th>
          </tr>
        </thead>
        <tbody>
          {items.map((check) => (
            <tr key={check.id} className="border-t border-line align-top">
              <td className="py-2 text-ink-900">{formatDateTime(check.created_at)}</td>
              <td className="py-2 text-ink-900">#{check.user_id}</td>
              <td className="py-2 text-ink-900">
                {check.subject_type} #{check.subject_id}
              </td>
              <td className="py-2 text-ink-900">{check.score.toFixed(2)}</td>
              <td className="py-2">
                <span
                  data-testid="fraud-decision-badge"
                  className={`rounded-tile px-2 py-0.5 text-caption font-semibold ${decisionBadgeClass(check.decision)}`}
                >
                  {decisionLabel(check.decision)}
                </span>
              </td>
              <td className="py-2 text-ink-500">
                {check.signals.map((signal) => signal.detail).join("; ")}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
