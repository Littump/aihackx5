import { ProgressBar } from "@/shared/ui/ProgressBar";
import type { ChallengeDetail } from "../api";
import { formatCompactReward, formatDeadline } from "../format";

type SideChallengeCardProps = {
  challenge: ChallengeDetail;
};

export function SideChallengeCard({ challenge }: SideChallengeCardProps) {
  return (
    <section className="flex shrink-0 flex-col gap-3 rounded-card bg-surface p-4 shadow-card">
      <div className="flex items-start justify-between gap-3">
        <h4 className="text-body font-semibold leading-tight">{challenge.title}</h4>
        <span className="shrink-0 rounded-tile bg-accent-50 px-3 py-1 text-caption font-semibold text-accent-700">
          {formatCompactReward(challenge.reward_xp, challenge.reward_points)}
        </span>
      </div>
      <ProgressBar value={challenge.progress} max={challenge.target} />
      <div className="flex items-center justify-between">
        <span className="text-caption text-ink-500">
          {challenge.progress} из {challenge.target}
        </span>
        <span className="text-caption text-ink-500">до {formatDeadline(challenge.period_end)}</span>
      </div>
    </section>
  );
}
