import { Card } from "@/shared/ui/Card";
import { formatMoney } from "@/shared/lib/format";
import { Stat } from "./Stat";
import { formatDateTime, formatDays, formatPercent } from "../format";
import type { PmUserResponse } from "../api";

type UserFeatures = PmUserResponse["features"];

type FeaturesBlockProps = {
  features: UserFeatures;
};

export function FeaturesBlock({ features }: FeaturesBlockProps) {
  return (
    <Card className="flex flex-col gap-3">
      <div>
        <h2 className="text-lead font-bold">Профиль и признаки</h2>
        <p className="mt-1 text-caption text-ink-500">
          Посчитано {formatDateTime(features.computed_at)} · окно {features.window_weeks} нед.
        </p>
      </div>
      <dl className="m-0 grid grid-cols-2 gap-3">
        <Stat label="Частота" value={`${features.frequency_per_week}/нед.`} />
        <Stat label="Давность" value={`${features.recency_days} дн.`} />
        <Stat label="Средний чек" value={formatMoney(features.avg_basket)} />
        <Stat label="Чувствительность к промо" value={formatPercent(features.promo_sensitivity)} />
        <Stat label="Ритм" value={formatDays(features.cadence_days)} />
        <Stat label="Экономия за 30 дней" value={formatMoney(features.realized_savings_30d)} />
        <Stat label="Любимый магазин" value={`#${features.favourite_store_id}`} />
        <Stat label="Покупки в других сетях" value={formatPercent(features.cross_chain_share)} />
      </dl>
      <CategoryAffinityTable categoryAffinity={features.category_affinity} />
    </Card>
  );
}

function CategoryAffinityTable({
  categoryAffinity,
}: {
  categoryAffinity: UserFeatures["category_affinity"];
}) {
  const categories = Object.entries(categoryAffinity);
  if (categories.length === 0) return null;

  return (
    <div>
      <p className="text-caption font-medium uppercase text-ink-500">Категории</p>
      <table className="mt-2 w-full text-body">
        <thead>
          <tr className="text-left text-caption text-ink-500">
            <th className="pb-1 pr-3 font-normal">Категория</th>
            <th className="pb-1 pr-3 font-normal">Доля</th>
            <th className="pb-1 pr-3 font-normal">Визитов</th>
            <th className="pb-1 font-normal">Каденс</th>
          </tr>
        </thead>
        <tbody>
          {categories.map(([category, affinity]) => (
            <tr key={category} className="border-t border-line">
              <td className="py-1 pr-3 text-ink-900">{category}</td>
              <td className="py-1 pr-3 text-ink-900">{formatPercent(affinity.share)}</td>
              <td className="py-1 pr-3 text-ink-900">{affinity.visits}</td>
              <td className="py-1 text-ink-900">{formatDays(affinity.cadence_days)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
