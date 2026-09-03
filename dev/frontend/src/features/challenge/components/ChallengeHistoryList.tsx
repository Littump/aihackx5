import type { ChallengeHistoryItem } from "../api";
import { formatDeadline, formatReward } from "../format";

type ChallengeHistoryListProps = {
  items: ChallengeHistoryItem[];
};

export function ChallengeHistoryList({ items }: ChallengeHistoryListProps) {
  if (items.length === 0) {
    return <p className="text-sm text-text-secondary">Пока нет выполненных челленджей.</p>;
  }

  return (
    <ul className="flex flex-col gap-2">
      {items.map((item) => (
        <li
          key={item.id}
          className="flex items-center justify-between rounded-xl border border-border bg-surface px-3 py-2"
        >
          <div>
            <p className="text-sm font-medium text-text">{item.title}</p>
            <p className="text-xs text-text-secondary">{formatDeadline(item.period_end)}</p>
          </div>
          <span className="text-xs font-medium text-legacy-accent-600">
            {formatReward(item.reward_xp, item.reward_points)}
          </span>
        </li>
      ))}
    </ul>
  );
}
