import { Card } from "@/shared/ui/Card";
import { ProgressBar } from "@/shared/ui/ProgressBar";
import { Badge } from "@/shared/ui/Badge";
import { DomovoyAvatar } from "@/features/domovoy/DomovoyAvatar";
import { MOOD_LABEL } from "@/features/domovoy/moodLabels";
import type { HomeResponse } from "../api";

type DomovoyHeaderProps = {
  domovoy: HomeResponse["domovoy"];
  justSimulated: boolean;
};

export function DomovoyHeader({ domovoy, justSimulated }: DomovoyHeaderProps) {
  const xpTotalForNextLevel = domovoy.xp + domovoy.xp_to_next_level;
  return (
    <Card className="flex items-center gap-4">
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
    </Card>
  );
}
