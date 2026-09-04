import type { ReactNode } from "react";
import { formatEventDate, formatSignedPoints, formatSignedXp } from "../format";
import type { RewardEvent } from "../api";

type RewardHistoryListProps = {
  items: RewardEvent[];
};

const KIND_ICON: Record<RewardEvent["kind"], ReactNode> = {
  receipt_xp: <path d="M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6M9 12h6" />,
  challenge: <path d="m4 13 5 5L20 7" />,
  streak: <path d="M12 3c3 3 4 5 4 8a4 4 0 0 1-8 0c0-3 1-5 4-8z" />,
  league: <path d="M7 4h10v5a5 5 0 0 1-10 0zM9 20h6M12 14v6" />,
  referral: (
    <>
      <circle cx="9" cy="8" r="3" />
      <path d="M3 20a6 6 0 0 1 12 0M17 11h4M19 9v4" />
    </>
  ),
  achievement: (
    <>
      <circle cx="12" cy="9" r="5" />
      <path d="m9 15-1 6 4-2 4 2-1-6" />
    </>
  ),
};

export function RewardHistoryList({ items }: RewardHistoryListProps) {
  if (items.length === 0) {
    return (
      <p className="text-body text-ink-500">
        Пока ничего не начислено. Первая же покупка добавит опыт Домовому.
      </p>
    );
  }

  return (
    <section className="flex shrink-0 flex-col divide-y divide-line rounded-card bg-surface shadow-card">
      {items.map((event) => (
        <div key={event.id} className="flex items-center gap-3 p-4">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-tile bg-brand-50 text-brand-700">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.75"
              strokeLinecap="round"
              className="h-6 w-6"
              aria-hidden="true"
            >
              {KIND_ICON[event.kind]}
            </svg>
          </span>
          <div className="flex min-w-0 flex-1 flex-col gap-1">
            <span className="text-body font-semibold leading-tight">{event.title}</span>
            <span className="text-caption text-ink-500">
              {formatEventDate(event.created_at)}
              {event.detail ? ` · ${event.detail}` : ""}
            </span>
          </div>
          <span className="flex shrink-0 flex-col items-end gap-1">
            {event.xp_delta !== 0 && (
              <span className="text-caption font-semibold text-brand-700">
                {formatSignedXp(event.xp_delta)}
              </span>
            )}
            {event.points_delta !== 0 && (
              <span className="text-caption font-semibold text-accent-700">
                {formatSignedPoints(event.points_delta)}
              </span>
            )}
          </span>
        </div>
      ))}
    </section>
  );
}
