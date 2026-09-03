import { Card } from "@/shared/ui/Card";
import { ProgressBar } from "@/shared/ui/ProgressBar";
import { formatDeadline } from "@/shared/lib/format";
import type { HomeResponse } from "../api";

type HeroChallenge = NonNullable<HomeResponse["hero_challenge"]>;

type HeroChallengeCardProps = {
  challenge: HeroChallenge;
  explanationOpen: boolean;
  onToggleExplanation: () => void;
};

export function HeroChallengeCard({
  challenge,
  explanationOpen,
  onToggleExplanation,
}: HeroChallengeCardProps) {
  return (
    <Card>
      <p className="text-xs font-medium uppercase text-legacy-accent-600">Цель недели</p>
      <h2 className="mt-1 text-lg font-semibold text-text">{challenge.title}</h2>
      <p className="mt-1 text-sm text-text-secondary">{challenge.body}</p>
      <div className="mt-3 flex items-center justify-between text-sm text-text">
        <span className="font-semibold">
          {challenge.progress} / {challenge.target}
        </span>
        <span className="text-text-secondary">до {formatDeadline(challenge.period_end)}</span>
      </div>
      <div className="mt-2">
        <ProgressBar value={challenge.progress} max={challenge.target} />
      </div>
      <p className="mt-2 text-sm font-medium text-legacy-brand-600">
        +{challenge.reward_xp} XP + {challenge.reward_points} баллов
      </p>
      <button
        type="button"
        onClick={onToggleExplanation}
        aria-expanded={explanationOpen}
        className="mt-3 text-sm font-medium text-legacy-brand-600 underline"
      >
        Почему это мне?
      </button>
      {explanationOpen && (
        <p className="mt-2 rounded-lg bg-legacy-brand-100 p-3 text-sm text-text">
          {challenge.explanation}
        </p>
      )}
    </Card>
  );
}
