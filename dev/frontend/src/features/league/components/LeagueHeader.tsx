import type { LeagueResponse } from "../api";
import { formatRankChangeMessage, formatWeekRange, zoneLabel } from "../format";
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
    <div
      data-testid="league-header"
      className="flex shrink-0 flex-col gap-3 bg-brand-700 px-4 py-4 text-white"
    >
      <div className="flex items-center gap-3">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          className="h-6 w-6"
          aria-hidden="true"
        >
          <path d="M15 5l-7 7 7 7" />
        </svg>
        <h1 className="text-lead font-bold">Лига домов</h1>
      </div>
      <p className="text-body text-brand-100">
        Дивизион {league.division} «{league.division_name}» · неделя{" "}
        {formatWeekRange(league.week_start, league.week_end)}
      </p>
      <div className="grid grid-cols-3 gap-3">
        <div className="flex flex-col gap-1 rounded-tile bg-brand-800 p-3">
          <span className="text-caption text-brand-100">Место</span>
          <span className="text-lead font-bold">
            {league.my_rank} из {league.size}
          </span>
        </div>
        <div className="flex flex-col gap-1 rounded-tile bg-brand-800 p-3">
          <span className="text-caption text-brand-100">Счёт</span>
          <span className="text-lead font-bold">{league.my_score}</span>
        </div>
        <div className="flex flex-col gap-1 rounded-tile bg-brand-800 p-3">
          <span className="text-caption text-brand-100">Зона</span>
          <span className="text-body font-bold">{zoneLabel(league.my_zone)}</span>
        </div>
      </div>
      {changed && (
        <div
          data-testid="rank-change"
          className="flex animate-popin items-center gap-2 self-start rounded-tile bg-white px-3 py-2 text-brand-700"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
            className="h-6 w-6"
            aria-hidden="true"
          >
            {improved ? <path d="M12 19V5M6 11l6-6 6 6" /> : <path d="M12 5v14M6 13l6 6 6-6" />}
          </svg>
          <span className="text-body font-semibold">
            {formatRankChangeMessage(rankChange!.before!, rankChange!.after!)}
          </span>
        </div>
      )}
    </div>
  );
}
