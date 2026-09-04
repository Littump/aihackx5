import { Card } from "@/shared/ui/Card";
import { formatMoney } from "@/shared/lib/format";
import { Stat } from "./Stat";
import { formatPercent } from "../format";
import { isNotFoundError, usePmSimulation } from "../hooks";
import type { SimulationRun } from "../api";

export function SimulationBlock() {
  const simulationQuery = usePmSimulation();

  return (
    <Card className="flex flex-col gap-3">
      <h2 className="text-lead font-bold">Симуляция: контроль и тест</h2>
      {simulationQuery.isPending && <p className="text-ink-500">Загрузка…</p>}
      {isNotFoundError(simulationQuery) && <p className="text-ink-500">Ещё не запускали.</p>}
      {simulationQuery.isError && !isNotFoundError(simulationQuery) && (
        <p className="text-accent-700">
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
      <div className="w-full overflow-x-auto">
        <table className="w-full min-w-[320px] border-collapse text-body">
          <thead>
            <tr className="text-left text-caption text-ink-500">
              <th className="py-2 font-normal">Показатель</th>
              <th className="py-2 font-normal">Контроль</th>
              <th className="py-2 font-normal">Тест</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-t border-line">
              <td className="py-2">Покупок на пользователя</td>
              <td className="py-2">{r.purchases_per_user_control.toFixed(2)}</td>
              <td className="py-2 font-semibold text-brand-700">
                {r.purchases_per_user_treatment.toFixed(2)}
              </td>
            </tr>
            <tr className="border-t border-line">
              <td className="py-2">Доля с N+ покупками</td>
              <td className="py-2">{formatPercent(r.share_above_n_control)}</td>
              <td className="py-2 font-semibold text-brand-700">
                {formatPercent(r.share_above_n_treatment)}
              </td>
            </tr>
            <tr className="border-t border-line">
              <td className="py-2">Прирост частоты</td>
              <td className="py-2">—</td>
              <td className="py-2 font-semibold text-brand-700">
                {formatPercent(r.frequency_uplift)}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <dl className="m-0 grid grid-cols-2 gap-3 border-t border-line pt-3">
        <Stat label="Доп. выручка" value={formatMoney(r.incremental_revenue)} />
        <Stat label="Доп. маржа" value={formatMoney(r.incremental_margin)} />
        <Stat label="Стоимость наград" value={formatMoney(r.reward_cost)} />
        <Stat
          label="Чистый эффект"
          value={formatMoney(r.net_effect)}
          valueClassName="text-brand-700"
        />
        <Stat label="Конверсия приглашений" value={formatPercent(r.referral_conversion)} />
        <Stat
          label="Точность / полнота антифрода"
          value={`${formatPercent(r.fraud_precision)} / ${formatPercent(r.fraud_recall)}`}
        />
      </dl>
      <AssumptionsList params={run.params} />
    </>
  );
}

function AssumptionsList({ params }: { params: Record<string, unknown> }) {
  const entries = Object.entries(params);
  if (entries.length === 0) return null;

  return (
    <div>
      <p className="text-caption font-medium uppercase text-ink-500">Допущения</p>
      <ul className="mt-1 text-body text-ink-900">
        {entries.map(([key, value]) => (
          <li key={key}>
            {key}: {String(value)}
          </li>
        ))}
      </ul>
    </div>
  );
}
