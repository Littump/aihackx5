import type { ReactNode } from "react";
import type { StatusChipStatus } from "@/shared/ui/StatusChip";
import type { ChallengeHistoryItem } from "../api";
import { formatChallengeHistoryStatus, formatCompactReward, formatDeadline } from "../format";

type ChallengeHistoryListProps = {
  items: ChallengeHistoryItem[];
};

const TONE_ICON: Record<StatusChipStatus, ReactNode> = {
  success: <path d="m4 13 5 5L20 7" />,
  inProgress: (
    <>
      <circle cx="12" cy="12" r="8" />
      <path d="M12 8v4l3 2" />
    </>
  ),
  failed: <path d="M6 6l12 12M18 6 6 18" />,
  neutral: (
    <>
      <circle cx="11" cy="11" r="6" />
      <path d="m16 16 4 4" />
    </>
  ),
};

const TONE_CIRCLE_CLASSES: Record<StatusChipStatus, string> = {
  success: "bg-brand-50 text-brand-700",
  inProgress: "bg-accent-50 text-accent-700",
  failed: "bg-canvas text-ink-500",
  neutral: "bg-canvas text-ink-500",
};

export function ChallengeHistoryList({ items }: ChallengeHistoryListProps) {
  if (items.length === 0) {
    return <p className="text-body text-ink-500">Пока нет выполненных челленджей.</p>;
  }

  return (
    <section className="flex shrink-0 flex-col divide-y divide-line rounded-card bg-surface shadow-card">
      {items.map((item) => {
        const status = formatChallengeHistoryStatus(item.status);
        const hasReward = item.status === "completed";
        return (
          <div key={item.id} className="flex items-center gap-3 p-4">
            <span
              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-tile ${TONE_CIRCLE_CLASSES[status.tone]}`}
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
                {TONE_ICON[status.tone]}
              </svg>
            </span>
            <div className="flex min-w-0 flex-1 flex-col gap-1">
              <span className="text-body font-semibold leading-tight">{item.title}</span>
              <span className="text-caption text-ink-500">
                {formatDeadline(item.period_end)} · {status.text}
              </span>
            </div>
            <span
              className={`shrink-0 text-caption ${hasReward ? "font-semibold text-brand-700" : "text-ink-500"}`}
            >
              {hasReward ? formatCompactReward(item.reward_xp, item.reward_points) : "без награды"}
            </span>
          </div>
        );
      })}
    </section>
  );
}
