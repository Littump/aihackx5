import { useSearchParams } from "react-router";
import { useUserContext } from "@/features/users/hooks";
import { DomovoyMessageScreen } from "@/features/domovoy/DomovoyMessageScreen";
import { Button } from "@/shared/ui/Button";
import { LinkButton } from "@/shared/ui/LinkButton";
import { NAV_ICON_PATHS } from "@/shared/ui/navIcons";
import { RetryButton } from "@/shared/ui/RetryButton";
import { ChallengeHistoryList } from "./components/ChallengeHistoryList";
import { ChallengeSkeleton } from "./components/ChallengeSkeleton";
import { HeroChallengeCard } from "./components/HeroChallengeCard";
import { SideChallengeCard } from "./components/SideChallengeCard";
import { useChallenges, useRefreshChallenges } from "./hooks";

const ERROR_BODY =
  "Домовой не дозвонился до кассы. Проверьте связь и попробуйте ещё раз — данные не потеряются.";

export function ChallengeScreen() {
  const { userId } = useUserContext();
  const [searchParams] = useSearchParams();
  const challenges = useChallenges(userId);
  const refresh = useRefreshChallenges(userId);
  const suffix = `?${searchParams.toString()}`;

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
        {challenges.isPending && <ChallengeSkeleton />}

        {challenges.isError && (
          <DomovoyMessageScreen
            mood="bored"
            heading="Не получилось загрузить"
            body={ERROR_BODY}
            className="flex-1 min-h-0"
          >
            <RetryButton onClick={() => challenges.refetch()} />
          </DomovoyMessageScreen>
        )}

        {isEmpty && (
          <DomovoyMessageScreen
            mood="sleepy"
            heading="Домовой думает над целью недели…"
            body="Ему нужна ещё одна ваша покупка, чтобы понять ваш ритм. Обычно это занимает пару дней."
            className="flex-1 min-h-0"
          >
            <Button
              onClick={() => refresh.mutate()}
              disabled={refresh.isPending}
              className="w-full"
            >
              {refresh.isPending ? "Обновляем…" : "Обновить"}
            </Button>
            <LinkButton to={`/${suffix}`}>Посмотреть экономию за месяц</LinkButton>
            <LinkButton to={`/referral${suffix}`} variant="secondary">
              Позвать соседа
            </LinkButton>
          </DomovoyMessageScreen>
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
