import { useUserContext } from "@/features/users/hooks";
import { DomovoyMessageScreen } from "@/features/domovoy/DomovoyMessageScreen";
import { Card } from "@/shared/ui/Card";
import { RetryButton } from "@/shared/ui/RetryButton";
import { ChallengeEconomicsBlock } from "./components/ChallengeEconomicsBlock";
import { EvalBlock } from "./components/EvalBlock";
import { FeaturesBlock } from "./components/FeaturesBlock";
import { FraudBlock } from "./components/FraudBlock";
import { LedgerBlock } from "./components/LedgerBlock";
import { MechanicBlock } from "./components/MechanicBlock";
import { PmSkeleton } from "./components/PmSkeleton";
import { SimulationBlock } from "./components/SimulationBlock";
import { UserFraudBlock } from "./components/UserFraudBlock";
import { usePmUser } from "./hooks";

export function PmScreen() {
  const { userId } = useUserContext();
  const pmUserQuery = usePmUser(userId);

  return (
    <section className="flex flex-1 flex-col gap-4">
      <h1 className="text-title font-bold text-ink-900">PM view — экран для продакта</h1>

      <div className="flex items-start gap-2 rounded-tile bg-accent-50 px-4 py-3 text-accent-700">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          className="h-6 w-6 shrink-0"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="9" />
          <path d="M12 8h.01M12 11v5" />
        </svg>
        <p className="m-0 text-body font-semibold">
          Допущения симуляции, не фактические показатели X5.
        </p>
      </div>

      {(userId === null || pmUserQuery.isPending) && <PmSkeleton />}

      {pmUserQuery.isError && (
        <Card>
          <DomovoyMessageScreen
            mood="bored"
            heading="Не получилось загрузить"
            body="Домовой не дозвонился до кассы. Проверьте связь и попробуйте ещё раз — данные не потеряются."
          >
            <RetryButton onClick={() => pmUserQuery.refetch()} />
          </DomovoyMessageScreen>
        </Card>
      )}

      {pmUserQuery.data && (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <FeaturesBlock features={pmUserQuery.data.features} />
            <MechanicBlock recommendedMechanic={pmUserQuery.data.recommended_mechanic} />
            <ChallengeEconomicsBlock
              heroChallenge={pmUserQuery.data.hero_challenge}
              rewardsTotalPoints={pmUserQuery.data.rewards_total_points}
              rewardsTotalXp={pmUserQuery.data.rewards_total_xp}
              expectedIncrementalMarginMonth={pmUserQuery.data.expected_incremental_margin_month}
            />
            <UserFraudBlock fraudChecks={pmUserQuery.data.fraud_checks} />
            <LedgerBlock ledger={pmUserQuery.data.ledger} />
            <SimulationBlock />
            <div className="md:col-span-2">
              <EvalBlock />
            </div>
          </div>
          <FraudBlock />
        </>
      )}
    </section>
  );
}
