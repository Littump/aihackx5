import { useState } from "react";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { useUserContext } from "@/features/users/hooks";
import { DomovoyHeader } from "./components/DomovoyHeader";
import { SavingsCard } from "./components/SavingsCard";
import { HeroChallengeCard } from "./components/HeroChallengeCard";
import { QuickLinks } from "./components/QuickLinks";
import { useHome, useSimulateReceipt } from "./hooks";

const FLASH_DURATION_MS = 900;

export function HomeScreen() {
  const { userId } = useUserContext();
  const homeQuery = useHome(userId);
  const simulate = useSimulateReceipt(userId);
  const [explanationOpen, setExplanationOpen] = useState(false);
  const [flash, setFlash] = useState(false);

  function handleSimulate() {
    simulate.mutate(undefined, {
      onSuccess: () => {
        setFlash(true);
        window.setTimeout(() => setFlash(false), FLASH_DURATION_MS);
      },
    });
  }

  if (userId === null || homeQuery.isPending) {
    return (
      <section className="flex flex-1 flex-col gap-4 p-5">
        <p className="text-text-secondary">Домовой просыпается…</p>
      </section>
    );
  }

  if (homeQuery.isError) {
    return (
      <section className="flex flex-1 flex-col gap-4 p-5">
        <p className="text-legacy-accent-600">
          Не получилось загрузить Home: {homeQuery.error.message}
        </p>
      </section>
    );
  }

  const home = homeQuery.data;

  return (
    <section className="flex flex-1 flex-col gap-4 p-5">
      <DomovoyHeader domovoy={home.domovoy} flash={flash} />
      <SavingsCard savings={home.savings} flash={flash} />
      <Card>
        <p className="text-xs font-medium uppercase text-text-secondary">Инсайт</p>
        <p className="mt-1 text-sm text-text">{home.insight}</p>
      </Card>
      {home.hero_challenge ? (
        <HeroChallengeCard
          challenge={home.hero_challenge}
          explanationOpen={explanationOpen}
          onToggleExplanation={() => setExplanationOpen((open) => !open)}
        />
      ) : (
        <Card>
          <p className="text-text-secondary">Домовой думает над целью недели…</p>
        </Card>
      )}
      <Button onClick={handleSimulate} disabled={simulate.isPending}>
        {simulate.isPending ? "Симулируем покупку…" : "Simulate new purchase"}
      </Button>
      {simulate.isError && (
        <p role="alert" className="text-sm text-legacy-accent-600">
          Не получилось: {simulate.error.message}
        </p>
      )}
      <QuickLinks league={home.league} referral={home.referral} />
    </section>
  );
}
