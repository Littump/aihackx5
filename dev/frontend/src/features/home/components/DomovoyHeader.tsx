import { Link, useSearchParams } from "react-router";
import { Card } from "@/shared/ui/Card";
import { ProgressBar } from "@/shared/ui/ProgressBar";
import { Badge } from "@/shared/ui/Badge";
import { DomovoyAvatar } from "@/features/domovoy/DomovoyAvatar";
import { MOOD_LABEL } from "@/features/domovoy/moodLabels";
import { formatPoints } from "@/features/rewards/format";
import type { HomeResponse } from "../api";

type DomovoyHeaderProps = {
  domovoy: HomeResponse["domovoy"];
  pointsBalance: number;
  justSimulated: boolean;
};

export function DomovoyHeader({ domovoy, pointsBalance, justSimulated }: DomovoyHeaderProps) {
  const [searchParams] = useSearchParams();
  const xpTotalForNextLevel = domovoy.xp + domovoy.xp_to_next_level;
  return (
    <Card className="flex flex-col gap-3">
      <div className="flex items-center gap-4">
        <DomovoyAvatar mood={domovoy.mood} size={80} level={domovoy.level} className="shrink-0" />
        <div className="flex min-w-0 flex-col gap-1">
          <h1 className="text-title font-bold leading-tight">Домовой</h1>
          <p className="text-body text-ink-700">
            Уровень {domovoy.level} · {MOOD_LABEL[domovoy.mood]} — {domovoy.mood_reason}
          </p>
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <div className="w-1/4 shrink-0">
              <ProgressBar value={domovoy.xp} max={xpTotalForNextLevel} tone="light" />
            </div>
            <span
              className={`whitespace-nowrap text-caption font-semibold ${
                justSimulated
                  ? "animate-glow rounded-tile bg-accent-50 px-2 py-1 text-accent-700"
                  : ""
              }`}
            >
              {domovoy.xp} XP
            </span>
            <span className="text-caption text-ink-500 whitespace-nowrap">
              ещё {domovoy.xp_to_next_level}
            </span>
            <Badge tone="brand" className="whitespace-nowrap">
              серия {domovoy.streak_weeks} нед.
            </Badge>
          </div>
        </div>
      </div>
      <Link
        to={`/rewards?${searchParams.toString()}`}
        className="flex items-center justify-between gap-2 border-t border-line pt-3 text-body font-semibold text-ink-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-700"
      >
        <span>{formatPoints(pointsBalance)} на счету</span>
        <span className="flex items-center gap-1 text-caption text-brand-700">
          За что начисляют
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
            className="h-5 w-5"
            aria-hidden="true"
          >
            <path d="m9 6 6 6-6 6" />
          </svg>
        </span>
      </Link>
    </Card>
  );
}
