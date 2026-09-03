import { Card } from "@/shared/ui/Card";
import { formatPercent } from "../format";
import { isNotFoundError, usePmEval } from "../hooks";
import type { EvalRun } from "../api";

export function EvalBlock() {
  const evalQuery = usePmEval();

  return (
    <Card>
      <h2 className="text-lg font-semibold text-text">Eval</h2>
      {evalQuery.isPending && <p className="mt-2 text-text-secondary">Загрузка…</p>}
      {isNotFoundError(evalQuery) && <p className="mt-2 text-text-secondary">Ещё не запускали.</p>}
      {evalQuery.isError && !isNotFoundError(evalQuery) && (
        <p className="mt-2 text-legacy-accent-600">
          Не удалось загрузить eval: {evalQuery.error.message}
        </p>
      )}
      {evalQuery.data && <EvalResults run={evalQuery.data} />}
    </Card>
  );
}

function EvalResults({ run }: { run: EvalRun }) {
  return (
    <>
      <p className="mt-1 text-xs text-text-secondary">{run.profiles} профилей</p>
      <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <MetricCard label="Hit rate" value={formatPercent(run.hit_rate)} />
        <MetricCard label="Invalid rate" value={formatPercent(run.invalid_rate)} />
        <MetricCard label="Fallback rate" value={formatPercent(run.fallback_rate)} />
        <MetricCard label="Economics pass rate" value={formatPercent(run.economics_pass_rate)} />
      </div>
      <ProfilesTable details={run.details} />
    </>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-legacy-brand-100 p-3">
      <p className="text-xs text-text-secondary">{label}</p>
      <p className="mt-1 text-lg font-semibold text-text">{value}</p>
    </div>
  );
}

function ProfilesTable({ details }: { details: Record<string, unknown>[] }) {
  if (details.length === 0) return null;
  const columns = Array.from(new Set(details.flatMap((row) => Object.keys(row))));

  return (
    <table className="mt-4 w-full text-sm">
      <thead>
        <tr className="text-left text-xs text-text-secondary">
          {columns.map((column) => (
            <th key={column} className="pb-1 font-normal">
              {column}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {details.map((row, index) => (
          <tr key={index} className="border-t border-border">
            {columns.map((column) => (
              <td key={column} className="py-1 text-text">
                {String(row[column] ?? "—")}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
