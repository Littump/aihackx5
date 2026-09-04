import { ProgressBar } from "@/shared/ui/ProgressBar";
import { formatDeadline } from "@/shared/lib/format";
import type { HomeResponse } from "../api";

type HeroChallenge = NonNullable<HomeResponse["hero_challenge"]>;

type HeroChallengeCardProps = {
  challenge: HeroChallenge;
  explanationOpen: boolean;
  onToggleExplanation: () => void;
  justSimulated: boolean;
};

export function HeroChallengeCard({
  challenge,
  explanationOpen,
  onToggleExplanation,
  justSimulated,
}: HeroChallengeCardProps) {
  return (
    <section className="flex shrink-0 flex-col gap-3 rounded-card bg-brand-700 p-4 text-white shadow-card">
      <div className="flex items-center gap-2">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          className="h-6 w-6"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="8" />
          <circle cx="12" cy="12" r="3" />
        </svg>
        <span className="text-caption font-semibold uppercase tracking-wider text-brand-100">
          Цель недели
        </span>
      </div>
      <h3 className="text-title font-bold leading-tight">{challenge.title}</h3>
      <p className="text-body text-pretty text-brand-100">{challenge.body}</p>
      <div className="flex flex-col gap-2">
        <ProgressBar value={challenge.progress} max={challenge.target} tone="dark" />
        <div className="flex justify-between text-body">
          <span
            className={`font-semibold ${
              justSimulated ? "animate-glow rounded-tile bg-white px-2 py-1 text-accent-700" : ""
            }`}
          >
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
          +{challenge.reward_xp} XP и {challenge.reward_points} баллов
        </span>
      </div>
      <button
        type="button"
        onClick={onToggleExplanation}
        aria-expanded={explanationOpen}
        className="flex items-center justify-between gap-2 rounded-tile bg-white px-4 py-3 text-body font-semibold text-brand-700"
      >
        <span>Почему это мне?</span>
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          className={`h-6 w-6 transition-transform ${explanationOpen ? "rotate-180" : ""}`}
          aria-hidden="true"
        >
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>
      {explanationOpen && (
        <p className="text-body text-pretty rounded-tile bg-brand-800 p-3 text-brand-100">
          {challenge.explanation}
        </p>
      )}
    </section>
  );
}
