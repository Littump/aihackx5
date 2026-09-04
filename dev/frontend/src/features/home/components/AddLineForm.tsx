import { useState } from "react";
import { Button } from "@/shared/ui/Button";
import { formatCategoryLabel } from "../categoryLabels";

type AddLineFormProps = {
  categories: string[];
  defaultPrice: number;
  disabled: boolean;
  onAdd: (category: string, price: number, isPromo: boolean) => void;
};

export function AddLineForm({ categories, defaultPrice, disabled, onAdd }: AddLineFormProps) {
  const [category, setCategory] = useState(categories[0] ?? "other");
  const [price, setPrice] = useState(defaultPrice);
  const [isPromo, setIsPromo] = useState(false);

  function handleAdd() {
    onAdd(category, price, isPromo);
    setPrice(defaultPrice);
    setIsPromo(false);
  }

  return (
    <div className="flex flex-col gap-2 rounded-tile border border-dashed border-line p-3">
      <p className="text-caption font-semibold uppercase tracking-wider text-ink-500">
        Добавить товар
      </p>
      <div className="flex gap-2">
        <label className="flex min-w-0 flex-1 flex-col gap-1">
          <span className="sr-only">Категория товара</span>
          <select
            value={category}
            onChange={(event) => setCategory(event.target.value)}
            className="w-full rounded-tile border border-line bg-surface px-2 py-2 text-body"
          >
            {categories.map((code) => (
              <option key={code} value={code}>
                {formatCategoryLabel(code)}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-1">
          <span className="sr-only">Цена нового товара</span>
          <input
            type="number"
            min={0}
            step={10}
            value={price}
            onChange={(event) => setPrice(Number(event.target.value))}
            className="w-20 rounded-tile border border-line bg-surface px-2 py-2 text-right text-body"
          />
          <span className="text-body text-ink-500">₽</span>
        </label>
      </div>
      <label className="flex items-center gap-2 text-body">
        <input
          type="checkbox"
          checked={isPromo}
          onChange={(event) => setIsPromo(event.target.checked)}
          className="h-5 w-5 accent-brand-700"
        />
        Куплен по акции
      </label>
      <Button variant="secondary" disabled={disabled} onClick={handleAdd}>
        Добавить в чек
      </Button>
    </div>
  );
}
