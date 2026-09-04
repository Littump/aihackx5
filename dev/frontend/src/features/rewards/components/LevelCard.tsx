import { Card } from "@/shared/ui/Card";
import { InfoHint } from "@/shared/ui/InfoHint";
import { ProgressBar } from "@/shared/ui/ProgressBar";
import { formatNumber } from "@/shared/lib/format";
import type { RewardsResponse } from "../api";

type LevelCardProps = {
  rewards: RewardsResponse;
};

export function LevelCard({ rewards }: LevelCardProps) {
  const xpTotalForNextLevel = rewards.xp + rewards.xp_to_next_level;
  const isMaxLevel = rewards.xp_to_next_level === 0;

  return (
    <Card className="flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <h2 className="text-caption text-ink-500">Опыт Домового</h2>
        <InfoHint label="Что такое опыт и уровни">
          XP — это опыт Домового. Он растёт от каждой засчитанной покупки и от выполненных целей, а
          на новый уровень нужно накопить всё больше опыта. Уровень ни на что не тратится: это
          память о том, как долго вы вместе.
        </InfoHint>
      </div>
      <p className="m-0 flex items-baseline gap-2">
        <span className="text-hero font-bold leading-none">Уровень {rewards.level}</span>
        <span className="text-body text-ink-500">{formatNumber(rewards.xp)} XP</span>
      </p>
      <ProgressBar value={rewards.xp} max={xpTotalForNextLevel} />
      <p className="m-0 text-caption text-ink-500">
        {isMaxLevel
          ? "Максимальный уровень — дальше расти некуда"
          : `До уровня ${rewards.level + 1} осталось ${formatNumber(rewards.xp_to_next_level)} XP`}
      </p>
    </Card>
  );
}
