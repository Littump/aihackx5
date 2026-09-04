import { useState } from "react";
import { Button } from "@/shared/ui/Button";
import { formatMoney } from "@/shared/lib/format";
import type { SimulateDraft, SimulateItemInput } from "../api";
import { AddLineForm } from "./AddLineForm";
import { GoalHint } from "./GoalHint";
import { ReceiptLineRow } from "./ReceiptLineRow";

const MAX_LINES = 20;

export type DraftLine = {
  key: number;
  productName: string | null;
  category: string;
  price: number;
  isPromo: boolean;
};

type ReceiptDraftFormProps = {
  draft: SimulateDraft;
  submitting: boolean;
  onCancel: () => void;
  onConfirm: (items: SimulateItemInput[]) => void;
};

export function ReceiptDraftForm({
  draft,
  submitting,
  onCancel,
  onConfirm,
}: ReceiptDraftFormProps) {
  const [lines, setLines] = useState<DraftLine[]>(() =>
    draft.items.map((item, index) => ({
      key: index,
      productName: item.product_name,
      category: item.category,
      price: item.price,
      isPromo: item.is_promo,
    })),
  );
  const [nextKey, setNextKey] = useState(draft.items.length);

  const goalCategory = draft.goal?.type === "category" ? draft.goal.category : null;
  const total = lines.reduce((sum, line) => sum + line.price, 0);
  const goalLines = goalCategory
    ? lines.filter((line) => line.category === goalCategory).length
    : 0;

  function addLine(category: string, price: number, isPromo: boolean) {
    setLines((current) => [
      ...current,
      { key: nextKey, productName: null, category, price, isPromo },
    ]);
    setNextKey((key) => key + 1);
  }

  function removeLine(key: number) {
    setLines((current) => current.filter((line) => line.key !== key));
  }

  function changePrice(key: number, price: number) {
    setLines((current) => current.map((line) => (line.key === key ? { ...line, price } : line)));
  }

  return (
    <>
      <GoalHint goal={draft.goal} goalLines={goalLines} />
      <ul className="m-0 flex list-none flex-col gap-2 p-0">
        {lines.map((line) => (
          <ReceiptLineRow
            key={line.key}
            line={line}
            matchesGoal={goalCategory !== null && line.category === goalCategory}
            onRemove={() => removeLine(line.key)}
            onPriceChange={(price) => changePrice(line.key, price)}
          />
        ))}
      </ul>
      {lines.length === 0 && (
        <p className="text-body text-ink-500">
          Чек пустой — добавьте хотя бы один товар, иначе покупки не будет.
        </p>
      )}
      <AddLineForm
        categories={draft.categories}
        defaultPrice={draft.default_price}
        disabled={lines.length >= MAX_LINES}
        onAdd={addLine}
      />
      <div className="sticky bottom-0 flex flex-col gap-2 border-t border-line bg-surface pt-3">
        <div className="flex items-center justify-between text-lead font-bold">
          <span>Итого</span>
          <span data-testid="receipt-total">{formatMoney(total)}</span>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" className="flex-1" onClick={onCancel}>
            Отмена
          </Button>
          <Button
            className="flex-1"
            disabled={submitting || lines.length === 0}
            onClick={() => onConfirm(lines.map(toItemInput))}
          >
            {submitting ? "Отправляем…" : "Подтвердить покупку"}
          </Button>
        </div>
      </div>
    </>
  );
}

function toItemInput(line: DraftLine): SimulateItemInput {
  return {
    product_name: line.productName,
    category: line.category,
    price: line.price,
    is_promo: line.isPromo,
  };
}
