import { formatCategoryLabel } from "../categoryLabels";
import type { DraftLine } from "./ReceiptDraftForm";

type ReceiptLineRowProps = {
  line: DraftLine;
  matchesGoal: boolean;
  onRemove: () => void;
  onPriceChange: (price: number) => void;
};

export function ReceiptLineRow({
  line,
  matchesGoal,
  onRemove,
  onPriceChange,
}: ReceiptLineRowProps) {
  const label = formatCategoryLabel(line.category);
  return (
    <li className="flex items-center gap-2 rounded-tile bg-canvas px-3 py-2">
      <div className="flex min-w-0 flex-1 flex-col">
        <span className="truncate text-body font-semibold">{line.productName ?? label}</span>
        <span className="flex flex-wrap items-center gap-1 text-caption text-ink-500">
          <span>{label}</span>
          {line.isPromo && <span className="whitespace-nowrap text-accent-700">−акция</span>}
          {matchesGoal && (
            <span className="whitespace-nowrap rounded-tile bg-brand-100 px-2 text-brand-700">
              к цели
            </span>
          )}
        </span>
      </div>
      <label className="flex items-center gap-1">
        <span className="sr-only">Цена: {line.productName ?? label}</span>
        <input
          type="number"
          min={0}
          step={10}
          value={line.price}
          onChange={(event) => onPriceChange(Number(event.target.value))}
          className="w-20 rounded-tile border border-line bg-surface px-2 py-1 text-right text-body"
        />
        <span className="text-body text-ink-500">₽</span>
      </label>
      <button
        type="button"
        onClick={onRemove}
        aria-label={`Удалить: ${line.productName ?? label}`}
        className="rounded-tile px-2 py-1 text-body text-ink-500 hover:bg-surface hover:text-accent-700"
      >
        ✕
      </button>
    </li>
  );
}
