import { useUserContext } from "@/features/users/hooks";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";
import { NAV_ICON_PATHS } from "@/shared/ui/navIcons";
import { ChallengeHistoryList } from "./components/ChallengeHistoryList";
import { HeroChallengeCard } from "./components/HeroChallengeCard";
import { SideChallengeCard } from "./components/SideChallengeCard";
import { useChallenges, useRefreshChallenges } from "./hooks";

export function ChallengeScreen() {
  const { userId } = useUserContext();
  const challenges = useChallenges(userId);
  const refresh = useRefreshChallenges(userId);

  const isEmpty =
    challenges.data !== undefined &&
    challenges.data.hero === null &&
    challenges.data.side.length === 0;

  return (
    <div className="flex h-full flex-col">
      <div className="flex shrink-0 items-center gap-3 border-b border-line bg-surface px-4 py-4">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          className="h-6 w-6"
          aria-hidden="true"
        >
          {NAV_ICON_PATHS.goal}
        </svg>
        <h1 className="text-lead font-bold">Цель недели</h1>
      </div>

      <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-4 py-4">
        {challenges.isPending && <p className="text-ink-500">Загрузка…</p>}

        {challenges.isError && (
          <p className="text-ink-500">Не удалось загрузить челленджи: {challenges.error.message}</p>
        )}

        {isEmpty && (
          <Card className="flex flex-col items-center gap-3 py-6 text-center">
            <p className="text-ink-700">Домовой думает над целью недели…</p>
            <Button onClick={() => refresh.mutate()} disabled={refresh.isPending}>
              {refresh.isPending ? "Обновляем…" : "Обновить"}
            </Button>
          </Card>
        )}

        {challenges.data && !isEmpty && (
          <>
            {challenges.data.hero !== null && (
              <HeroChallengeCard challenge={challenges.data.hero} />
            )}

            {challenges.data.side.length > 0 && (
              <>
                <h3 className="text-lead font-bold">Ещё можно взять</h3>
                {challenges.data.side.map((challenge) => (
                  <SideChallengeCard key={challenge.id} challenge={challenge} />
                ))}
              </>
            )}

            <h3 className="text-lead font-bold">История целей</h3>
            <ChallengeHistoryList items={challenges.data.history} />
          </>
        )}
      </div>
    </div>
  );
}
