import { Card } from "@/shared/ui/Card";
import { formatPercent } from "../format";
import { isNotFoundError, usePmEval } from "../hooks";
import type { EvalRun } from "../api";

export function EvalBlock() {
  const evalQuery = usePmEval();

  return (
    <Card className="flex flex-col gap-3">
      <h2 className="text-lead font-bold">Качество подбора целей ИИ</h2>
      {evalQuery.isPending && <p className="text-ink-500">Загрузка…</p>}
      {isNotFoundError(evalQuery) && <p className="text-ink-500">Ещё не запускали.</p>}
      {evalQuery.isError && !isNotFoundError(evalQuery) && (
        <p className="text-accent-700">Не удалось загрузить eval: {evalQuery.error.message}</p>
      )}
      {evalQuery.data && <EvalResults run={evalQuery.data} />}
    </Card>
  );
}

function EvalResults({ run }: { run: EvalRun }) {
  return (
    <>
      <dl className="m-0 grid grid-cols-2 gap-3 md:grid-cols-5">
        <MetricTile label="Профилей проверено" value={String(run.profiles)} />
        <MetricTile
          label="Попадание"
          value={formatPercent(run.hit_rate)}
          valueClassName="text-brand-700"
        />
        <MetricTile
          label="Некорректных"
          value={formatPercent(run.invalid_rate)}
          valueClassName="text-accent-700"
        />
        <MetricTile
          label="Шаблонных текстов"
          value={formatPercent(run.fallback_rate)}
          valueClassName="text-accent-700"
        />
        <MetricTile
          label="Прошли проверку экономики"
          value={formatPercent(run.economics_pass_rate)}
          valueClassName="text-brand-700"
        />
      </dl>
      <ProfilesTable details={run.details} />
    </>
  );
}

function MetricTile({
  label,
  value,
  valueClassName = "",
}: {
  label: string;
  value: string;
  valueClassName?: string;
}) {
  return (
    <div className="flex flex-col gap-1 rounded-tile bg-brand-50 p-3">
      <dt className="text-caption text-ink-500">{label}</dt>
      <dd className={`m-0 text-title font-bold text-ink-900 ${valueClassName}`}>{value}</dd>
    </div>
  );
}

function ProfilesTable({ details }: { details: Record<string, unknown>[] }) {
  if (details.length === 0) return null;
  const columns = Array.from(new Set(details.flatMap((row) => Object.keys(row))));

  return (
    <table className="w-full border-collapse text-body">
      <thead>
        <tr className="text-left text-caption text-ink-500">
          {columns.map((column) => (
            <th key={column} className="py-2 font-normal">
              {column}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {details.map((row, index) => (
          <tr key={index} className="border-t border-line">
            {columns.map((column) => (
              <td key={column} className="py-2 text-ink-900">
                {String(row[column] ?? "—")}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
