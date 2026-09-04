import { Card } from "@/shared/ui/Card";
import {
  decisionBadgeClass,
  decisionLabel,
  FRAUD_BLOCK_THRESHOLD,
  FRAUD_HOLD_THRESHOLD,
} from "../format";
import type { FraudCheck } from "../api";

type FraudSignal = FraudCheck["signals"][number];

type UserFraudBlockProps = {
  fraudChecks: FraudCheck[];
};

export function UserFraudBlock({ fraudChecks }: UserFraudBlockProps) {
  const latest = latestCheck(fraudChecks);

  return (
    <Card className="flex flex-col gap-3">
      <h2 className="text-lead font-bold">Антифрод</h2>
      {latest === null ? (
        <p className="text-ink-500">Проверок пока не было.</p>
      ) : (
        <>
          <div className="flex items-baseline gap-3">
            <span
              data-testid="user-fraud-score"
              className="text-hero font-bold leading-none text-ink-900"
            >
              {latest.score.toFixed(2)}
            </span>
            <span
              data-testid="user-fraud-decision-badge"
              className={`rounded-tile px-3 py-1 text-caption font-semibold ${decisionBadgeClass(latest.decision)}`}
            >
              {decisionLabel(latest.decision)}
            </span>
          </div>
          <FraudGauge score={latest.score} />
          <SignalsList signals={latest.signals} />
        </>
      )}
    </Card>
  );
}

function latestCheck(checks: FraudCheck[]): FraudCheck | null {
  if (checks.length === 0) return null;
  return [...checks].sort((a, b) => b.created_at.localeCompare(a.created_at))[0];
}

function FraudGauge({ score }: { score: number }) {
  const clamped = Math.min(Math.max(score, 0), 1);
  return (
    <div className="flex flex-col gap-1">
      <div className="relative h-3 w-full overflow-hidden rounded-tile bg-canvas">
        <div
          data-testid="fraud-gauge-fill"
          className="h-full rounded-tile bg-accent-500"
          style={{ width: `${clamped * 100}%` }}
        />
      </div>
      <GaugeMark testId="fraud-gauge-tick-hold" position={FRAUD_HOLD_THRESHOLD} label="порог 0,5" />
      <GaugeMark
        testId="fraud-gauge-tick-block"
        position={FRAUD_BLOCK_THRESHOLD}
        label="порог 0,8"
      />
      <GaugeMark
        testId="fraud-gauge-tick-current"
        position={clamped}
        label={`текущий ${score.toFixed(2)}`}
        strong
      />
      <div className="flex justify-between text-caption text-ink-500">
        <span>0</span>
        <span>1</span>
      </div>
    </div>
  );
}

type GaugeMarkProps = {
  testId: string;
  position: number;
  label: string;
  strong?: boolean;
};

function GaugeMark({ testId, position, label, strong = false }: GaugeMarkProps) {
  return (
    <div
      className={`relative flex text-caption ${strong ? "font-semibold text-ink-900" : "text-ink-500"}`}
    >
      <div data-testid={testId} className="shrink-0" style={{ width: `${position * 100}%` }} />
      <span className="whitespace-nowrap">{label}</span>
    </div>
  );
}

function SignalsList({ signals }: { signals: FraudSignal[] }) {
  if (signals.length === 0) return <p className="text-ink-500">Сигналов нет.</p>;

  return (
    <ul className="m-0 flex list-none flex-col gap-2 pl-0">
      {signals.map((signal, index) => (
        <li
          key={`${signal.code}-${index}`}
          className="flex items-start justify-between gap-3 border-t border-line pt-2"
        >
          <span className="text-body text-ink-700">
            {signal.detail} — вес {signal.weight}
          </span>
          <span
            className={`shrink-0 rounded-tile px-3 py-1 text-caption font-semibold ${
              signal.strong ? "bg-accent-50 text-accent-700" : "bg-canvas text-ink-700"
            }`}
          >
            {signal.strong ? "сильный" : "слабый"}
          </span>
        </li>
      ))}
    </ul>
  );
}
