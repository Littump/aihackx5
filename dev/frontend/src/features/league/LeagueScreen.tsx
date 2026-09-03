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
      <section className="flex flex-1 flex-col gap-4 p-5">
        <p className="text-text-secondary">Загружаем таблицу лиги…</p>
      </section>
    );
  }

  if (leagueQuery.isError) {
    return (
      <section className="flex flex-1 flex-col gap-4 p-5">
        <p className="text-accent-600">Не получилось загрузить лигу: {leagueQuery.error.message}</p>
      </section>
    );
  }

  const league = leagueQuery.data;

  return (
    <section className="flex flex-1 flex-col gap-4 p-5">
      <h1 className="text-2xl font-semibold text-text">Лига домов</h1>
      <LeagueHeader league={league} rankChange={rankChange} />
      <LeaderboardList league={league} />
      <HouseVsDistrictCard house={league.house} />
    </section>
  );
}
