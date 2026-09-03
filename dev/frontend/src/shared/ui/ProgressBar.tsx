type ProgressBarTone = "light" | "dark";

type ProgressBarProps = {
  value: number;
  max: number;
  tone?: ProgressBarTone;
};

const TRACK_CLASSES: Record<ProgressBarTone, string> = {
  light: "bg-brand-50",
  dark: "bg-brand-700",
};

const FILL_CLASSES: Record<ProgressBarTone, string> = {
  light: "bg-brand-600",
  dark: "bg-white",
};

export function ProgressBar({ value, max, tone = "light" }: ProgressBarProps) {
  const percent = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0;
  return (
    <div
      className={`h-3 w-full overflow-hidden rounded-tile ${TRACK_CLASSES[tone]}`}
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={max}
    >
      <div
        className={`h-full rounded-tile ${FILL_CLASSES[tone]}`}
        style={{ width: `${percent}%` }}
      />
    </div>
  );
}
