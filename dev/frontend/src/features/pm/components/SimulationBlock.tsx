import { Card } from "@/shared/ui/Card";
import { formatMoney } from "@/shared/lib/format";
import { formatPercent } from "../format";
import { isNotFoundError, usePmSimulation } from "../hooks";
import type { SimulationRun } from "../api";

export function SimulationBlock() {
  const simulationQuery = usePmSimulation();

  return (
    <Card>
      <h2 className="text-lg font-semibold text-text">Симуляция</h2>
      {simulationQuery.isPending && <p className="mt-2 text-text-secondary">Загрузка…</p>}
      {isNotFoundError(simulationQuery) && (
        <p className="mt-2 text-text-secondary">Ещё не запускали.</p>
      )}
      {simulationQuery.isError && !isNotFoundError(simulationQuery) && (
        <p className="mt-2 text-accent-600">
          Не удалось загрузить симуляцию: {simulationQuery.error.message}
        </p>
      )}
      {simulationQuery.data && <SimulationResults run={simulationQuery.data} />}
    </Card>
  );
}

function SimulationResults({ run }: { run: SimulationRun }) {
  const r = run.results;
  return (
    <>
      <p className="mt-1 text-xs text-text-secondary">
        Все показатели — simulation assumptions, не реальные данные X5.
      </p>
      <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
        <MetricCard
          label="Покупок на юзера (control)"
          value={r.purchases_per_user_control.toFixed(2)}
        />
        <MetricCard
          label="Покупок на юзера (treatment)"
          value={r.purchases_per_user_treatment.toFixed(2)}
        />
        <MetricCard label="Доля ≥N (control)" value={formatPercent(r.share_above_n_control)} />
        <MetricCard label="Доля ≥N (treatment)" value={formatPercent(r.share_above_n_treatment)} />
        <MetricCard label="Frequency uplift" value={formatPercent(r.frequency_uplift)} />
        <MetricCard label="Incremental revenue" value={formatMoney(r.incremental_revenue)} />
        <MetricCard label="Incremental margin" value={formatMoney(r.incremental_margin)} />
        <MetricCard label="Reward cost" value={formatMoney(r.reward_cost)} />
        <MetricCard label="Net effect" value={formatMoney(r.net_effect)} />
        <MetricCard label="Referral conversion" value={formatPercent(r.referral_conversion)} />
        <MetricCard label="Fraud precision" value={formatPercent(r.fraud_precision)} />
        <MetricCard label="Fraud recall" value={formatPercent(r.fraud_recall)} />
      </div>
      <AssumptionsList params={run.params} />
    </>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-brand-100 p-3">
      <p className="text-xs text-text-secondary">{label}</p>
      <p className="mt-1 text-lg font-semibold text-text">{value}</p>
    </div>
  );
}

function AssumptionsList({ params }: { params: Record<string, unknown> }) {
  const entries = Object.entries(params);
  if (entries.length === 0) return null;

  return (
    <div className="mt-4">
      <p className="text-xs font-medium uppercase text-text-secondary">Assumptions</p>
      <ul className="mt-1 text-sm text-text">
        {entries.map(([key, value]) => (
          <li key={key}>
            {key}: {String(value)}
          </li>
        ))}
      </ul>
    </div>
  );
}
