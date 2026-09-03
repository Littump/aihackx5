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
    <Card>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text">Антифрод</h2>
        <select
          aria-label="Фильтр по решению"
          value={decision ?? ""}
          onChange={handleChange}
          className="rounded-lg border border-border bg-surface px-2 py-1 text-sm text-text"
        >
          {DECISION_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {fraudQuery.isPending && <p className="mt-2 text-text-secondary">Загрузка…</p>}
      {fraudQuery.isError && (
        <p className="mt-2 text-legacy-accent-600">
          Не удалось загрузить проверки: {fraudQuery.error.message}
        </p>
      )}
      {fraudQuery.data && <FraudTable items={fraudQuery.data.items} />}
    </Card>
  );
}

function FraudTable({ items }: { items: FraudCheck[] }) {
  if (items.length === 0) return <p className="mt-2 text-text-secondary">Проверок нет.</p>;

  return (
    <table className="mt-3 w-full text-sm">
      <thead>
        <tr className="text-left text-xs text-text-secondary">
          <th className="pb-1 font-normal">Когда</th>
          <th className="pb-1 font-normal">Пользователь</th>
          <th className="pb-1 font-normal">Объект</th>
          <th className="pb-1 font-normal">Score</th>
          <th className="pb-1 font-normal">Решение</th>
          <th className="pb-1 font-normal">Сигналы</th>
        </tr>
      </thead>
      <tbody>
        {items.map((check) => (
          <tr key={check.id} className="border-t border-border align-top">
            <td className="py-1 text-text">{formatDateTime(check.created_at)}</td>
            <td className="py-1 text-text">#{check.user_id}</td>
            <td className="py-1 text-text">
              {check.subject_type} #{check.subject_id}
            </td>
            <td className="py-1 text-text">{check.score.toFixed(2)}</td>
            <td className="py-1">
              <span
                data-testid="fraud-decision-badge"
                className={`rounded-full px-2 py-0.5 text-xs font-semibold ${decisionBadgeClass(check.decision)}`}
              >
                {decisionLabel(check.decision)}
              </span>
            </td>
            <td className="py-1 text-text-secondary">
              {check.signals.map((signal) => signal.detail).join("; ")}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
