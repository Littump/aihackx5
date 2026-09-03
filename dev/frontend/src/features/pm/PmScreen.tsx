import { useUserContext } from "@/features/users/hooks";
import { Card } from "@/shared/ui/Card";
import { ChallengeEconomicsBlock } from "./components/ChallengeEconomicsBlock";
import { EvalBlock } from "./components/EvalBlock";
import { FeaturesBlock } from "./components/FeaturesBlock";
import { FraudBlock } from "./components/FraudBlock";
import { LedgerBlock } from "./components/LedgerBlock";
import { MechanicBlock } from "./components/MechanicBlock";
import { SimulationBlock } from "./components/SimulationBlock";
import { usePmUser } from "./hooks";

export function PmScreen() {
  const { userId } = useUserContext();
  const pmUserQuery = usePmUser(userId);

  return (
    <section className="flex flex-1 flex-col gap-4">
      <h1 className="text-2xl font-semibold text-text">PM view</h1>

      {(userId === null || pmUserQuery.isPending) && (
        <Card>
          <p className="text-text-secondary">Загрузка данных пользователя…</p>
        </Card>
      )}

      {pmUserQuery.isError && (
        <Card>
          <p className="text-legacy-accent-600">
            Не удалось загрузить PM-карточку: {pmUserQuery.error.message}
          </p>
        </Card>
      )}

      {pmUserQuery.data && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <FeaturesBlock features={pmUserQuery.data.features} />
          <MechanicBlock recommendedMechanic={pmUserQuery.data.recommended_mechanic} />
          <ChallengeEconomicsBlock
            heroChallenge={pmUserQuery.data.hero_challenge}
            rewardsTotalPoints={pmUserQuery.data.rewards_total_points}
            rewardsTotalXp={pmUserQuery.data.rewards_total_xp}
            expectedIncrementalMarginMonth={pmUserQuery.data.expected_incremental_margin_month}
          />
          <LedgerBlock ledger={pmUserQuery.data.ledger} />
          <FraudBlock />
          <SimulationBlock />
          <EvalBlock />
        </div>
      )}
    </section>
  );
}
