import { Card } from "@/shared/ui/Card";
import { formatMoney } from "@/shared/lib/format";
import { formatPercent } from "../format";
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
    <Card>
      <h2 className="text-lg font-semibold text-text">Челлендж и экономика</h2>
      {heroChallenge === null ? (
        <p className="mt-2 text-text-secondary">Активного hero-челленджа нет.</p>
      ) : (
        <ChallengeEconomicsDetails challenge={heroChallenge} />
      )}
      <table className="mt-4 w-full border-t border-border pt-2 text-sm">
        <tbody>
          <Row
            label="Выдано за всё время"
            value={`${rewardsTotalXp} XP + ${rewardsTotalPoints} баллов`}
          />
          <Row
            label="Ожидаемая margin за месяц"
            value={formatMoney(expectedIncrementalMarginMonth)}
          />
        </tbody>
      </table>
    </Card>
  );
}

type HeroChallenge = NonNullable<PmUserResponse["hero_challenge"]>;

function ChallengeEconomicsDetails({ challenge }: { challenge: HeroChallenge }) {
  return (
    <>
      <p className="mt-1 text-sm font-medium text-text">{challenge.title}</p>
      <table className="mt-2 w-full text-sm">
        <tbody>
          <Row label="Baseline" value={String(challenge.baseline)} />
          <Row label="Target" value={String(challenge.target)} />
          <Row label="Прогресс" value={String(challenge.progress)} />
          <Row
            label="Ожидаемая incremental margin"
            value={formatMoney(challenge.economics.expected_incremental_margin)}
          />
          <Row label="Max reward" value={formatMoney(challenge.economics.max_reward_rub)} />
          <Row
            label="Contribution margin"
            value={formatPercent(challenge.economics.contribution_margin)}
          />
          <Row
            label="Reward share max"
            value={formatPercent(challenge.economics.reward_share_max)}
          />
        </tbody>
      </table>
    </>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <tr className="border-t border-border">
      <td className="py-1 text-text-secondary">{label}</td>
      <td className="py-1 text-right font-medium text-text">{value}</td>
    </tr>
  );
}
