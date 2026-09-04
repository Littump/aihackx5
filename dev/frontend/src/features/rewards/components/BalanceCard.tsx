import { Card } from "@/shared/ui/Card";
import { InfoHint } from "@/shared/ui/InfoHint";
import { formatNumber } from "@/shared/lib/format";
import { pluralizePoints } from "../format";
import type { RewardsResponse } from "../api";

type BalanceCardProps = {
  rewards: RewardsResponse;
};

export function BalanceCard({ rewards }: BalanceCardProps) {
  return (
    <Card className="flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <h2 className="text-caption text-ink-500">Бонусные баллы</h2>
        <InfoHint label="Откуда берутся баллы">
          Баллы приходят за выполненные цели недели и за приглашённых соседей. За обычную покупку
          баллов нет — только опыт Домовому. Один балл равен одному рублю скидки.
        </InfoHint>
      </div>
      <p className="m-0 flex items-baseline gap-2">
        <span className="text-hero font-bold leading-none">
          {formatNumber(rewards.points_balance)}
        </span>
        <span className="text-body text-ink-500">{pluralizePoints(rewards.points_balance)}</span>
      </p>
    </Card>
  );
}
