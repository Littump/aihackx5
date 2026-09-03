import { useState } from "react";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";
import { DomovoyAvatar } from "@/features/domovoy/DomovoyAvatar";
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
      <section className="flex flex-1 flex-col gap-3 px-4 py-3">
        <p className="text-ink-500">Домовой просыпается…</p>
      </section>
    );
  }

  if (homeQuery.isError) {
    return (
      <section className="flex flex-1 flex-col gap-3 px-4 py-3">
        <p className="text-accent-700">
          Не получилось загрузить главный экран: {homeQuery.error.message}
        </p>
      </section>
    );
  }

  const home = homeQuery.data;

  return (
    <section className="flex flex-1 flex-col gap-3 px-4 py-3">
      <DomovoyHeader domovoy={home.domovoy} flash={flash} />
      <SavingsCard savings={home.savings} flash={flash} />
      {home.hero_challenge ? (
        <HeroChallengeCard
          challenge={home.hero_challenge}
          explanationOpen={explanationOpen}
          onToggleExplanation={() => setExplanationOpen((open) => !open)}
        />
      ) : (
        <Card>
          <p className="text-ink-500">Домовой думает над целью недели…</p>
        </Card>
      )}
      <section className="flex shrink-0 items-start gap-3 rounded-card bg-brand-50 p-4">
        <DomovoyAvatar mood="cheerful" size={48} className="shrink-0" />
        <div className="flex flex-col gap-1">
          <p className="text-caption font-semibold uppercase tracking-wider text-brand-700">
            Домовой заметил
          </p>
          <p className="text-body text-pretty text-ink-900">{home.insight}</p>
        </div>
      </section>
      <QuickLinks league={home.league} referral={home.referral} />
      <Button onClick={handleSimulate} disabled={simulate.isPending}>
        {simulate.isPending ? "Симулируем покупку…" : "Симулировать покупку"}
      </Button>
      {simulate.isError && (
        <p role="alert" className="text-body text-accent-700">
          Не получилось: {simulate.error.message}
        </p>
      )}
    </section>
  );
}
