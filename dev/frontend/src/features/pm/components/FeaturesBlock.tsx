import { Card } from "@/shared/ui/Card";
import { formatMoney } from "@/shared/lib/format";
import { formatDateTime, formatPercent } from "../format";
import type { PmUserResponse } from "../api";

type UserFeatures = PmUserResponse["features"];

type FeaturesBlockProps = {
  features: UserFeatures;
};

export function FeaturesBlock({ features }: FeaturesBlockProps) {
  return (
    <Card>
      <h2 className="text-lg font-semibold text-text">Features</h2>
      <p className="mt-1 text-xs text-text-secondary">
        Посчитано {formatDateTime(features.computed_at)} · окно {features.window_weeks} нед.
      </p>
      <FeaturesTable features={features} />
      <CategoryAffinityTable categoryAffinity={features.category_affinity} />
    </Card>
  );
}

function FeaturesTable({ features }: { features: UserFeatures }) {
  return (
    <table className="mt-3 w-full text-sm">
      <tbody>
        <FeatureRow label="Частота покупок" value={`${features.frequency_per_week}/нед.`} />
        <FeatureRow label="Давность последней покупки" value={`${features.recency_days} дн.`} />
        <FeatureRow label="Средний чек" value={formatMoney(features.avg_basket)} />
        <FeatureRow
          label="Чувствительность к промо"
          value={formatPercent(features.promo_sensitivity)}
        />
        <FeatureRow label="Каденс покупок" value={`${features.cadence_days} дн.`} />
        <FeatureRow
          label="Экономия за 30 дней"
          value={formatMoney(features.realized_savings_30d)}
        />
        <FeatureRow label="Любимый магазин" value={`#${features.favourite_store_id}`} />
        <FeatureRow
          label="Доля покупок вне сети"
          value={formatPercent(features.cross_chain_share)}
        />
      </tbody>
    </table>
  );
}

function FeatureRow({ label, value }: { label: string; value: string }) {
  return (
    <tr className="border-t border-border">
      <td className="py-1 text-text-secondary">{label}</td>
      <td className="py-1 text-right font-medium text-text">{value}</td>
    </tr>
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
    <div className="mt-4">
      <p className="text-xs font-medium uppercase text-text-secondary">Категории</p>
      <table className="mt-2 w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-text-secondary">
            <th className="pb-1 font-normal">Категория</th>
            <th className="pb-1 font-normal">Доля</th>
            <th className="pb-1 font-normal">Визитов</th>
            <th className="pb-1 font-normal">Каденс</th>
          </tr>
        </thead>
        <tbody>
          {categories.map(([category, affinity]) => (
            <tr key={category} className="border-t border-border">
              <td className="py-1 text-text">{category}</td>
              <td className="py-1 text-text">{formatPercent(affinity.share)}</td>
              <td className="py-1 text-text">{affinity.visits}</td>
              <td className="py-1 text-text">{affinity.cadence_days} дн.</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
