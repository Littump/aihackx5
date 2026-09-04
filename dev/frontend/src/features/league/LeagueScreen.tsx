import { useUserContext } from "@/features/users/hooks";
import { DomovoyMessageScreen } from "@/features/domovoy/DomovoyMessageScreen";
import { RetryButton } from "@/shared/ui/RetryButton";
import { HouseVsDistrictCard } from "./components/HouseVsDistrictCard";
import { LeaderboardList } from "./components/LeaderboardList";
import { LeagueHeader } from "./components/LeagueHeader";
import { LeagueSkeleton } from "./components/LeagueSkeleton";
import { useLeague, useLeagueRankChange } from "./hooks";

export function LeagueScreen() {
  const { userId } = useUserContext();
  const leagueQuery = useLeague(userId);
  const rankChange = useLeagueRankChange(userId);

  if (userId === null || leagueQuery.isPending) {
    return <LeagueSkeleton />;
  }

  if (leagueQuery.isError) {
    return (
      <DomovoyMessageScreen
        mood="bored"
        heading="Не получилось загрузить"
        body="Домовой не дозвонился до кассы. Проверьте связь и попробуйте ещё раз — данные не потеряются."
        className="flex-1 min-h-0 overflow-y-auto px-4 py-4"
      >
        <RetryButton onClick={() => leagueQuery.refetch()} />
      </DomovoyMessageScreen>
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
          В рейтинге — реальные покупатели вашего магазина. Персональные данные скрыты: только
          псевдоним, уровень и очки — без имён, адресов и сумм чужих покупок.
        </p>
        <LeaderboardList league={league} />
        <HouseVsDistrictCard house={league.house} />
      </div>
    </div>
  );
}
