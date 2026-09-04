import { useState } from "react";
import { Card } from "@/shared/ui/Card";
import { formatMoney, formatNumber, formatSignedMoney } from "@/shared/lib/format";
import { formatCategoryLabel } from "../categoryLabels";
import type { HomeResponse } from "../api";

type SavingsCardProps = {
  savings: HomeResponse["savings"];
  justSimulated: boolean;
};

export function SavingsCard({ savings, justSimulated }: SavingsCardProps) {
  const [open, setOpen] = useState(false);
  const isPositiveDelta = savings.delta >= 0;
  const maxCategoryAmount = Math.max(1, ...savings.top_categories.map((item) => item.amount));

  return (
    <Card className="flex flex-col gap-2">
      <h3 className="text-caption text-ink-500">Экономия за месяц</h3>
      <p className="m-0 flex flex-wrap items-baseline gap-2">
        <span
          className={`text-hero font-bold leading-none ${
            justSimulated ? "animate-glow rounded-tile bg-accent-50 px-2 py-1 text-accent-700" : ""
          }`}
        >
          {formatMoney(savings.amount)}
        </span>
        <span
          className={`text-body font-semibold ${isPositiveDelta ? "text-brand-700" : "text-accent-700"}`}
        >
          {formatSignedMoney(savings.delta)} к прошлому месяцу
        </span>
      </p>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="flex items-center justify-between gap-2 border-t border-line pt-2 text-body font-semibold text-ink-700"
      >
        <span>Из чего сложилось</span>
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          className={`h-6 w-6 transition-transform ${open ? "rotate-180" : ""}`}
          aria-hidden="true"
        >
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>
      {open && (
        <div className="flex flex-col gap-3 pt-1">
          <dl className="m-0 flex flex-col gap-2">
            <div className="flex justify-between text-body">
              <dt className="text-ink-700">Скидки</dt>
              <dd className="m-0 font-semibold">{formatMoney(savings.discount_amount)}</dd>
            </div>
            <div className="flex justify-between text-body">
              <dt className="text-ink-700">Начислено баллов</dt>
              <dd className="m-0 font-semibold">{formatNumber(savings.points_earned)}</dd>
            </div>
            <div className="flex justify-between text-body">
              <dt className="text-ink-700">Потрачено баллов</dt>
              <dd className="m-0 font-semibold">{formatNumber(savings.points_spent)}</dd>
            </div>
          </dl>
          <div className="flex flex-col gap-2 border-t border-line pt-3">
            <p className="text-caption text-ink-500">Топ-категории</p>
            {savings.top_categories.map((item) => (
              <div key={item.category} className="flex flex-col gap-1">
                <div className="flex justify-between text-body">
                  <span>{formatCategoryLabel(item.category)}</span>
                  <span className="font-semibold">{formatMoney(item.amount)}</span>
                </div>
                <div className="h-2 rounded-tile bg-brand-50">
                  <div
                    className="h-full rounded-tile bg-brand-500"
                    style={{ width: `${Math.round((item.amount / maxCategoryAmount) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}
