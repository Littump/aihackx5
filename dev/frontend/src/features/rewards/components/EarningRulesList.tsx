import { formatNumber } from "@/shared/lib/format";
import { formatRulePoints } from "../format";
import type { RewardRule } from "../api";

type EarningRulesListProps = {
  rules: RewardRule[];
};

export function EarningRulesList({ rules }: EarningRulesListProps) {
  return (
    <section className="flex shrink-0 flex-col divide-y divide-line rounded-card bg-surface shadow-card">
      {rules.map((rule) => {
        const points = formatRulePoints(rule.points_min, rule.points_max);
        return (
          <div key={rule.code} className="flex items-center gap-3 p-4">
            <span className="min-w-0 flex-1 text-body text-pretty">{rule.title}</span>
            <span className="flex shrink-0 flex-col items-end gap-1">
              <span className="text-caption font-semibold text-brand-700">
                +{formatNumber(rule.xp)} XP
              </span>
              {points && (
                <span className="text-caption font-semibold text-accent-700">{points}</span>
              )}
            </span>
          </div>
        );
      })}
    </section>
  );
}
