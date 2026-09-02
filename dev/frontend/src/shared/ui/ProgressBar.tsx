type ProgressBarTone = "brand" | "accent";

type ProgressBarProps = {
  value: number;
  max: number;
  tone?: ProgressBarTone;
};

const TONE_CLASSES: Record<ProgressBarTone, string> = {
  brand: "bg-brand-600",
  accent: "bg-accent-600",
};

export function ProgressBar({ value, max, tone = "brand" }: ProgressBarProps) {
  const percent = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0;
  return (
    <div
      className="h-2 w-full overflow-hidden rounded-full bg-brand-100"
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={max}
    >
      <div
        className={`h-full rounded-full ${TONE_CLASSES[tone]}`}
        style={{ width: `${percent}%` }}
      />
    </div>
  );
}
