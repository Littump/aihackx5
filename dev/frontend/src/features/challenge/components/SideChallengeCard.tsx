import { Card } from "@/shared/ui/Card";
import { ProgressBar } from "@/shared/ui/ProgressBar";
import type { ChallengeDetail } from "../api";
import { formatChallengeType, formatDeadline, formatReward } from "../format";
import { ExplanationDisclosure } from "./ExplanationDisclosure";

type SideChallengeCardProps = {
  challenge: ChallengeDetail;
};

export function SideChallengeCard({ challenge }: SideChallengeCardProps) {
  return (
    <Card>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text">{challenge.title}</h3>
        <span className="text-xs text-text-secondary">{formatChallengeType(challenge.type)}</span>
      </div>
      <p className="mt-1 text-xs text-text-secondary">{challenge.body}</p>
      <p className="mt-2 text-xs text-text">
        {challenge.baseline} → <span className="font-semibold">{challenge.target}</span>
      </p>
      <div className="mt-2">
        <ProgressBar value={challenge.progress} max={challenge.target} />
        <p className="mt-1 text-xs text-text-secondary">
          {challenge.progress} / {challenge.target} · до {formatDeadline(challenge.period_end)}
        </p>
      </div>
      <p className="mt-1 text-xs font-medium text-legacy-accent-600">
        {formatReward(challenge.reward_xp, challenge.reward_points)}
      </p>
      <div className="mt-2">
        <ExplanationDisclosure explanation={challenge.explanation} />
      </div>
    </Card>
  );
}
