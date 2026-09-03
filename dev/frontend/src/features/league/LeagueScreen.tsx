import { useUserContext } from "@/features/users/hooks";
import { HouseVsDistrictCard } from "./components/HouseVsDistrictCard";
import { LeaderboardList } from "./components/LeaderboardList";
import { LeagueHeader } from "./components/LeagueHeader";
import { useLeague, useLeagueRankChange } from "./hooks";

export function LeagueScreen() {
  const { userId } = useUserContext();
  const leagueQuery = useLeague(userId);
  const rankChange = useLeagueRankChange(userId);

  if (userId === null || leagueQuery.isPending) {
    return (
      <section className="flex flex-1 flex-col gap-4 px-4 py-4">
        <p className="text-ink-500">Загружаем таблицу лиги…</p>
      </section>
    );
  }

  if (leagueQuery.isError) {
    return (
      <section className="flex flex-1 flex-col gap-4 px-4 py-4">
        <p className="text-accent-700">Не получилось загрузить лигу: {leagueQuery.error.message}</p>
      </section>
    );
  }

  const league = leagueQuery.data;

  return (
    <div className="flex h-full flex-col">
      <LeagueHeader league={league} rankChange={rankChange} />
      <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-4 py-4">
        <p className="m-0 flex items-start gap-2 text-pretty text-caption text-ink-700">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
            className="h-6 w-6 shrink-0 text-ink-500"
            aria-hidden="true"
          >
            <rect x="5" y="11" width="14" height="9" rx="2" />
            <path d="M8 11V8a4 4 0 0 1 8 0v3" />
          </svg>
          Показываем только псевдонимы и очки. Ни имён, ни адресов, ни сумм и состава чужих покупок.
        </p>
        <LeaderboardList league={league} />
        <HouseVsDistrictCard house={league.house} />
      </div>
    </div>
  );
}
