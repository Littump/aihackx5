import { Card } from "@/shared/ui/Card";
import { InfoHint } from "@/shared/ui/InfoHint";
import { formatNumber } from "@/shared/lib/format";
import { formatPoints, pluralizePoints } from "../format";
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
          Баллы копятся за выполненные цели недели и за приглашённых соседей, а ещё сюда попадают
          баллы, которые начислила или списала касса по вашему чеку. Один балл равен одному рублю
          скидки.
        </InfoHint>
      </div>
      <p className="m-0 flex items-baseline gap-2">
        <span className="text-hero font-bold leading-none">
          {formatNumber(rewards.points_balance)}
        </span>
        <span className="text-body text-ink-500">{pluralizePoints(rewards.points_balance)}</span>
      </p>
      <dl className="m-0 flex flex-col gap-2 border-t border-line pt-3">
        <div className="flex justify-between gap-2 text-body">
          <dt className="text-ink-700">За цели и приглашения</dt>
          <dd className="m-0 font-semibold">{formatPoints(rewards.points_from_rewards)}</dd>
        </div>
        <div className="flex justify-between gap-2 text-body">
          <dt className="text-ink-700">По чекам X5 Клуба</dt>
          <dd className="m-0 font-semibold">{formatPoints(rewards.points_from_receipts)}</dd>
        </div>
      </dl>
    </Card>
  );
}
