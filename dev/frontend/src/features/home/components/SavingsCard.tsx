import { Card } from "@/shared/ui/Card";
import { formatMoney, formatSignedMoney } from "@/shared/lib/format";
import type { HomeResponse } from "../api";

type SavingsCardProps = {
  savings: HomeResponse["savings"];
  flash: boolean;
};

export function SavingsCard({ savings, flash }: SavingsCardProps) {
  const isPositiveDelta = savings.delta >= 0;
  return (
    <Card
      className={
        flash ? "bg-accent-100 transition-colors duration-700" : "transition-colors duration-700"
      }
    >
      <p className="text-sm text-text-secondary">Экономия за месяц</p>
      <p className="text-2xl font-semibold text-text">{formatMoney(savings.amount)}</p>
      <p
        className={`text-sm font-medium ${isPositiveDelta ? "text-brand-600" : "text-accent-600"}`}
      >
        {formatSignedMoney(savings.delta)} к прошлому месяцу
      </p>
    </Card>
  );
}
