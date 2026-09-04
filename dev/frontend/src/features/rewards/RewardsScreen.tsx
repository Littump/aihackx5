import { Link, useSearchParams } from "react-router";
import { useUserContext } from "@/features/users/hooks";
import { DomovoyMessageScreen } from "@/features/domovoy/DomovoyMessageScreen";
import { RetryButton } from "@/shared/ui/RetryButton";
import { Skeleton } from "@/shared/ui/Skeleton";
import { BalanceCard } from "./components/BalanceCard";
import { EarningRulesList } from "./components/EarningRulesList";
import { LevelCard } from "./components/LevelCard";
import { RewardHistoryList } from "./components/RewardHistoryList";
import { useRewards } from "./hooks";

const ERROR_BODY =
  "Домовой не дозвонился до кассы. Проверьте связь и попробуйте ещё раз — данные не потеряются.";

export function RewardsScreen() {
  const { userId } = useUserContext();
  const [searchParams] = useSearchParams();
  const rewards = useRewards(userId);

  return (
    <div className="flex h-full flex-col">
      <div className="flex shrink-0 items-center gap-3 border-b border-line bg-surface px-4 py-4">
        <Link
          to={`/?${searchParams.toString()}`}
          aria-label="Вернуться на главную"
          className="flex h-8 w-8 items-center justify-center rounded-tile text-ink-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-700"
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
            <path d="m15 6-6 6 6 6" />
          </svg>
        </Link>
        <h1 className="text-lead font-bold">Баллы и опыт</h1>
      </div>

      <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-4 py-4">
        {rewards.isPending && (
          <>
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-48 w-full" />
          </>
        )}

        {rewards.isError && (
          <DomovoyMessageScreen
            mood="bored"
            heading="Не получилось загрузить"
            body={ERROR_BODY}
            className="flex-1 min-h-0"
          >
            <RetryButton onClick={() => rewards.refetch()} />
          </DomovoyMessageScreen>
        )}

        {rewards.data && (
          <>
            <BalanceCard rewards={rewards.data} />
            <LevelCard rewards={rewards.data} />
            <h2 className="text-lead font-bold">За что начисляем</h2>
            <EarningRulesList rules={rewards.data.rules} />
            <h2 className="text-lead font-bold">История начислений</h2>
            <RewardHistoryList items={rewards.data.history} />
          </>
        )}
      </div>
    </div>
  );
}
