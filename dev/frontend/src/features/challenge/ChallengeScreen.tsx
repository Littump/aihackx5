import { useUserContext } from "@/features/users/hooks";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";
import { ChallengeHistoryList } from "./components/ChallengeHistoryList";
import { HeroChallengeCard } from "./components/HeroChallengeCard";
import { SideChallengeCard } from "./components/SideChallengeCard";
import { useChallenges, useRefreshChallenges } from "./hooks";

export function ChallengeScreen() {
  const { userId } = useUserContext();
  const challenges = useChallenges(userId);
  const refresh = useRefreshChallenges(userId);

  return (
    <section className="flex flex-1 flex-col gap-5 p-5">
      <h1 className="text-2xl font-semibold text-text">Челлендж</h1>

      {challenges.isPending && <p className="text-text-secondary">Загрузка…</p>}

      {challenges.isError && (
        <p className="text-text-secondary">
          Не удалось загрузить челленджи: {challenges.error.message}
        </p>
      )}

      {challenges.data && (
        <>
          {challenges.data.hero === null && challenges.data.side.length === 0 && (
            <Card className="flex flex-col items-center gap-3 py-6 text-center">
              <p className="text-text">Домовой думает…</p>
              <Button onClick={() => refresh.mutate()} disabled={refresh.isPending}>
                {refresh.isPending ? "Обновляем…" : "Обновить"}
              </Button>
            </Card>
          )}

          {challenges.data.hero !== null && <HeroChallengeCard challenge={challenges.data.hero} />}

          {challenges.data.side.length > 0 && (
            <div className="flex flex-col gap-3">
              {challenges.data.side.map((challenge) => (
                <SideChallengeCard key={challenge.id} challenge={challenge} />
              ))}
            </div>
          )}

          <div className="flex flex-col gap-2">
            <h2 className="text-lg font-semibold text-text">История</h2>
            <ChallengeHistoryList items={challenges.data.history} />
          </div>
        </>
      )}
    </section>
  );
}
