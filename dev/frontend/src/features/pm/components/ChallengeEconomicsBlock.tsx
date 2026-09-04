import { Card } from "@/shared/ui/Card";
import { formatMoney } from "@/shared/lib/format";
import { Stat } from "./Stat";
import type { PmUserResponse } from "../api";

type ChallengeEconomicsBlockProps = {
  heroChallenge: PmUserResponse["hero_challenge"];
  rewardsTotalPoints: number;
  rewardsTotalXp: number;
  expectedIncrementalMarginMonth: number;
};

export function ChallengeEconomicsBlock({
  heroChallenge,
  rewardsTotalPoints,
  rewardsTotalXp,
  expectedIncrementalMarginMonth,
}: ChallengeEconomicsBlockProps) {
  return (
    <Card className="flex flex-col gap-3">
      <h2 className="text-lead font-bold">Экономика цели</h2>
      {heroChallenge === null ? (
        <p className="text-ink-500">Активного hero-челленджа нет.</p>
      ) : (
        <ChallengeEconomicsDetails challenge={heroChallenge} />
      )}
      <dl className="m-0 grid grid-cols-2 gap-3 border-t border-line pt-3">
        <Stat
          label="Выдано за всё время"
          value={`${rewardsTotalXp} XP + ${rewardsTotalPoints} баллов`}
        />
        <Stat
          label="Ожидаемая margin за месяц"
          value={formatMoney(expectedIncrementalMarginMonth)}
        />
      </dl>
    </Card>
  );
}

type HeroChallenge = NonNullable<PmUserResponse["hero_challenge"]>;

function ChallengeEconomicsDetails({ challenge }: { challenge: HeroChallenge }) {
  const economics = challenge.economics;
  return (
    <div className="flex flex-col gap-3">
      <p className="text-body font-semibold text-ink-900">{challenge.title}</p>
      <dl className="m-0 grid grid-cols-3 gap-3">
        <Stat label="Baseline" value={String(challenge.baseline)} />
        <Stat label="Target" value={String(challenge.target)} />
        <Stat label="Прогресс" value={String(challenge.progress)} />
      </dl>
      <dl className="m-0 grid grid-cols-2 gap-3">
        <Stat label="Средний чек" value={formatMoney(economics.avg_basket)} />
        <Stat
          label="Ожидаемые доп. покупки"
          value={String(economics.expected_incremental_purchases)}
        />
        <Stat
          label="Ожидаемая доп. маржа"
          value={formatMoney(economics.expected_incremental_margin)}
        />
        <Stat label="Максимальный бюджет награды" value={formatMoney(economics.max_reward_rub)} />
        <Stat label="Выданная награда" value={`${challenge.reward_points} баллов`} />
      </dl>
      <BudgetIndicator
        rewardPoints={challenge.reward_points}
        maxRewardRub={economics.max_reward_rub}
      />
    </div>
  );
}

function BudgetIndicator({
  rewardPoints,
  maxRewardRub,
}: {
  rewardPoints: number;
  maxRewardRub: number;
}) {
  const withinBudget = rewardPoints <= maxRewardRub;
  const tone = withinBudget ? "bg-brand-50 text-brand-700" : "bg-accent-50 text-accent-700";
  const message = withinBudget
    ? `Награда укладывается в бюджет: ${rewardPoints} из ${formatMoney(maxRewardRub)}`
    : `Награда превышает бюджет: ${rewardPoints} из ${formatMoney(maxRewardRub)}`;

  return (
    <div className={`flex items-center gap-2 rounded-tile px-3 py-3 ${tone}`}>
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        className="h-6 w-6 shrink-0"
        aria-hidden="true"
      >
        {withinBudget ? <path d="m4 13 5 5L20 7" /> : <path d="M12 8v5M12 16h.01" />}
      </svg>
      <span className="text-body font-semibold">{message}</span>
    </div>
  );
}
