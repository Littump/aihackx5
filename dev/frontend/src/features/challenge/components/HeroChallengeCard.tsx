import { ProgressBar } from "@/shared/ui/ProgressBar";
import type { ChallengeDetail } from "../api";
import { formatChallengeType, formatDeadline, formatReward } from "../format";

type HeroChallengeCardProps = {
  challenge: ChallengeDetail;
};

export function HeroChallengeCard({ challenge }: HeroChallengeCardProps) {
  return (
    <section className="flex shrink-0 flex-col gap-3 rounded-card bg-brand-700 p-4 text-white shadow-card">
      <span className="text-caption font-semibold uppercase tracking-wider text-brand-100">
        {formatChallengeType(challenge.type)}
      </span>
      <h3 className="text-title font-bold leading-tight">{challenge.title}</h3>
      <p className="text-body text-pretty text-brand-100">{challenge.body}</p>
      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1 rounded-tile bg-brand-800 p-3">
          <span className="text-caption text-brand-100">Ваша обычная норма</span>
          <span className="text-lead font-bold">{challenge.baseline}</span>
        </div>
        <div className="flex flex-col gap-1 rounded-tile bg-brand-800 p-3">
          <span className="text-caption text-brand-100">Цель</span>
          <span className="text-lead font-bold">{challenge.target}</span>
        </div>
      </div>
      <div className="flex flex-col gap-2">
        <ProgressBar value={challenge.progress} max={challenge.target} tone="dark" />
        <div className="flex justify-between text-body">
          <span className="font-semibold">
            {challenge.progress} из {challenge.target}
          </span>
          <span className="text-brand-100">до {formatDeadline(challenge.period_end)}</span>
        </div>
      </div>
      <div className="flex items-center gap-2 self-start rounded-tile bg-white px-3 py-2 text-accent-700">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          className="h-6 w-6"
          aria-hidden="true"
        >
          <path d="M20 12v7a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-7M3 8h18v4H3zM12 8v12M12 8S10 3 7.5 4.5 12 8 12 8s2-5 4.5-3.5S12 8 12 8" />
        </svg>
        <span className="text-body font-semibold">
          {formatReward(challenge.reward_xp, challenge.reward_points)}
        </span>
      </div>
      <div className="flex flex-col gap-1 rounded-tile bg-brand-800 p-3">
        <p className="text-caption font-semibold text-brand-100">Почему это мне?</p>
        <p className="text-body text-pretty text-white">{challenge.explanation}</p>
      </div>
    </section>
  );
}
