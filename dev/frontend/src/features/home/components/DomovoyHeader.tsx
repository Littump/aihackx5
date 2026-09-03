import { Card } from "@/shared/ui/Card";
import { ProgressBar } from "@/shared/ui/ProgressBar";
import { DomovoyAvatar } from "@/features/domovoy/DomovoyAvatar";
import { MOOD_LABEL } from "@/features/domovoy/moodLabels";
import type { HomeResponse } from "../api";

type DomovoyHeaderProps = {
  domovoy: HomeResponse["domovoy"];
  flash: boolean;
};

export function DomovoyHeader({ domovoy, flash }: DomovoyHeaderProps) {
  const xpTotalForNextLevel = domovoy.xp + domovoy.xp_to_next_level;
  return (
    <Card
      className={
        flash ? "bg-accent-100 transition-colors duration-700" : "transition-colors duration-700"
      }
    >
      <div className="flex items-center gap-3">
        <DomovoyAvatar mood={domovoy.mood} size={80} level={domovoy.level} className="shrink-0" />
        <div className="flex-1">
          <h1 className="text-lg font-semibold text-text">Домовой · уровень {domovoy.level}</h1>
          <p className="text-sm text-text-secondary">
            {MOOD_LABEL[domovoy.mood]} · {domovoy.mood_reason}
          </p>
        </div>
      </div>
      <div className="mt-3">
        <div className="mb-1 flex justify-between text-xs text-text-secondary">
          <span>XP {domovoy.xp}</span>
          <span>
            до уровня {domovoy.level + 1}: {xpTotalForNextLevel}
          </span>
        </div>
        <ProgressBar value={domovoy.xp} max={xpTotalForNextLevel} />
      </div>
    </Card>
  );
}
