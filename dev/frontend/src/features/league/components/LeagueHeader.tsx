import { Card } from "@/shared/ui/Card";
import type { LeagueResponse } from "../api";
import { formatWeekRange, zoneBadgeClass, zoneLabel } from "../format";
import type { LeagueRankChange } from "../hooks";

type LeagueHeaderProps = {
  league: LeagueResponse;
  rankChange: LeagueRankChange | null;
};

export function LeagueHeader({ league, rankChange }: LeagueHeaderProps) {
  const changed =
    rankChange !== null &&
    rankChange.before !== null &&
    rankChange.after !== null &&
    rankChange.before !== rankChange.after;
  const improved = changed && rankChange.after! < rankChange.before!;

  return (
    <Card
      className={
        changed ? "bg-accent-100 transition-colors duration-700" : "transition-colors duration-700"
      }
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase text-text-secondary">Дивизион {league.division}</p>
          <h2 className="text-lg font-semibold capitalize text-text">{league.division_name}</h2>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-xs font-semibold ${zoneBadgeClass(league.my_zone)}`}
        >
          {zoneLabel(league.my_zone)}
        </span>
      </div>
      <p className="mt-1 text-xs text-text-secondary">
        Неделя {formatWeekRange(league.week_start, league.week_end)}
      </p>
      <p className="mt-3 text-2xl font-semibold text-text">
        Место {league.my_rank}{" "}
        <span className="text-sm font-normal text-text-secondary">из {league.size}</span>
      </p>
      <p className="text-sm text-text-secondary">Очки: {league.my_score}</p>
      {changed && (
        <p
          className={`mt-2 text-sm font-medium ${improved ? "text-legacy-brand-600" : "text-legacy-accent-600"}`}
        >
          {improved ? "▲" : "▼"} Место изменилось: {rankChange.before} → {rankChange.after}
        </p>
      )}
    </Card>
  );
}
