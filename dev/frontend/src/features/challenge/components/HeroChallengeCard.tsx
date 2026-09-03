import { Card } from "@/shared/ui/Card";
import { ProgressBar } from "@/shared/ui/ProgressBar";
import type { ChallengeDetail } from "../api";
import { formatChallengeType, formatDeadline, formatReward } from "../format";
import { ExplanationDisclosure } from "./ExplanationDisclosure";

type HeroChallengeCardProps = {
  challenge: ChallengeDetail;
};

export function HeroChallengeCard({ challenge }: HeroChallengeCardProps) {
  return (
    <Card className="border-legacy-brand-600 bg-legacy-brand-100">
      <div className="flex items-center justify-between">
        <span className="rounded-full bg-legacy-brand-600 px-2 py-0.5 text-xs font-semibold text-white">
          Главный челлендж
        </span>
        <span className="text-xs text-text-secondary">{formatChallengeType(challenge.type)}</span>
      </div>
      <h2 className="mt-2 text-lg font-semibold text-text">{challenge.title}</h2>
      <p className="mt-1 text-sm text-text-secondary">{challenge.body}</p>
      <p className="mt-3 text-sm text-text">
        {challenge.baseline} → <span className="font-semibold">{challenge.target}</span>
      </p>
      <div className="mt-2">
        <ProgressBar value={challenge.progress} max={challenge.target} />
        <p className="mt-1 text-xs text-text-secondary">
          {challenge.progress} / {challenge.target}
        </p>
      </div>
      <p className="mt-2 text-xs text-text-secondary">
        Дедлайн: {formatDeadline(challenge.period_end)}
      </p>
      <p className="mt-1 text-sm font-medium text-legacy-accent-600">
        {formatReward(challenge.reward_xp, challenge.reward_points)}
      </p>
      <div className="mt-3">
        <ExplanationDisclosure explanation={challenge.explanation} />
      </div>
    </Card>
  );
}
