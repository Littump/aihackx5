import { Fragment } from "react";
import type { LeagueResponse } from "../api";
import { isDemotionBoundary, isPromotionBoundary, zoneForRank } from "../format";
import { LeaderboardRow } from "./LeaderboardRow";

type LeaderboardListProps = {
  league: LeagueResponse;
};

export function LeaderboardList({ league }: LeaderboardListProps) {
  const members = [...league.members].sort((a, b) => a.rank - b.rank);

  return (
    <section
      data-testid="leaderboard"
      className="shrink-0 overflow-hidden rounded-card bg-surface shadow-card"
    >
      <div className="flex items-center gap-3 border-b border-line px-4 py-3 text-caption text-ink-500">
        <span className="w-8">№</span>
        <span className="flex-1">Сосед</span>
        <span>Счёт</span>
      </div>
      {members.map((member) => (
        <Fragment key={member.rank}>
          {isDemotionBoundary(member.rank, league.demotion_cutoff) && (
            <div className="flex items-center gap-2 bg-accent-50 px-4 py-2 text-accent-700">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.75"
                strokeLinecap="round"
                className="h-6 w-6"
                aria-hidden="true"
              >
                <path d="M12 5v14M6 13l6 6 6-6" />
              </svg>
              <span className="text-caption font-semibold">
                Ниже — понижение в дивизион {league.division - 1}
              </span>
            </div>
          )}
          <LeaderboardRow
            member={member}
            zone={zoneForRank(member.rank, league.promotion_cutoff, league.demotion_cutoff)}
          />
          {isPromotionBoundary(member.rank, league.promotion_cutoff) && (
            <div className="flex items-center gap-2 bg-brand-50 px-4 py-2 text-brand-700">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.75"
                strokeLinecap="round"
                className="h-6 w-6"
                aria-hidden="true"
              >
                <path d="M12 19V5M6 11l6-6 6 6" />
              </svg>
              <span className="text-caption font-semibold">
                Выше — повышение в дивизион {league.division + 1}
              </span>
            </div>
          )}
        </Fragment>
      ))}
    </section>
  );
}
