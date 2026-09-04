import { useRef, useState } from "react";
import { useSearchParams } from "react-router";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";
import { LinkButton } from "@/shared/ui/LinkButton";
import { RetryButton } from "@/shared/ui/RetryButton";
import { DomovoyAvatar } from "@/features/domovoy/DomovoyAvatar";
import { DomovoyMessageScreen } from "@/features/domovoy/DomovoyMessageScreen";
import { useUserContext } from "@/features/users/hooks";
import { DomovoyHeader } from "./components/DomovoyHeader";
import { HomeSkeleton } from "./components/HomeSkeleton";
import { SavingsCard } from "./components/SavingsCard";
import { HeroChallengeCard } from "./components/HeroChallengeCard";
import { QuickLinks } from "./components/QuickLinks";
import { useHome, useSimulateReceipt } from "./hooks";

const HIGHLIGHT_DURATION_MS = 3300;

export function HomeScreen() {
  const { userId } = useUserContext();
  const [searchParams] = useSearchParams();
  const homeQuery = useHome(userId);
  const simulate = useSimulateReceipt(userId);
  const [explanationOpen, setExplanationOpen] = useState(false);
  const [justSimulated, setJustSimulated] = useState(false);
  const highlightTimeoutRef = useRef<number | undefined>(undefined);

  function handleSimulate() {
    simulate.mutate(undefined, {
      onSuccess: () => {
        window.clearTimeout(highlightTimeoutRef.current);
        setJustSimulated(true);
        highlightTimeoutRef.current = window.setTimeout(
          () => setJustSimulated(false),
          HIGHLIGHT_DURATION_MS,
        );
      },
    });
  }

  if (userId === null || homeQuery.isPending) {
    return <HomeSkeleton />;
  }

  if (homeQuery.isError) {
    return (
      <DomovoyMessageScreen
        mood="bored"
        heading="Не получилось загрузить"
        body="Домовой не дозвонился до кассы. Проверьте связь и попробуйте ещё раз — данные не потеряются."
        className="flex-1 min-h-0 overflow-y-auto px-4 py-4"
      >
        <RetryButton onClick={() => homeQuery.refetch()} />
      </DomovoyMessageScreen>
    );
  }

  const home = homeQuery.data;
  const suffix = `?${searchParams.toString()}`;

  return (
    <section className="flex flex-1 flex-col gap-3 px-4 py-3">
      <DomovoyHeader domovoy={home.domovoy} justSimulated={justSimulated} />
      <SavingsCard savings={home.savings} justSimulated={justSimulated} />
      {home.hero_challenge ? (
        <HeroChallengeCard
          challenge={home.hero_challenge}
          explanationOpen={explanationOpen}
          onToggleExplanation={() => setExplanationOpen((open) => !open)}
          justSimulated={justSimulated}
        />
      ) : (
        <Card>
          <DomovoyMessageScreen
            mood="sleepy"
            heading="Домовой думает над целью недели…"
            body="Ему нужна ещё одна ваша покупка, чтобы понять ваш ритм. Обычно это занимает пару дней."
            avatarSize={80}
          >
            <LinkButton to={`/referral${suffix}`} variant="secondary">
              Позвать соседа
            </LinkButton>
          </DomovoyMessageScreen>
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
          Не получилось отправить покупку. Попробуйте ещё раз.
        </p>
      )}
    </section>
  );
}
