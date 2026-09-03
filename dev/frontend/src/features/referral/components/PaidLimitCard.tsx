import { ProgressBar } from "@/shared/ui/ProgressBar";
import { limitText } from "../format";

type PaidLimitCardProps = {
  paidThisMonth: number;
  paidLimitMonth: number;
};

export function PaidLimitCard({ paidThisMonth, paidLimitMonth }: PaidLimitCardProps) {
  return (
    <section className="flex shrink-0 flex-col gap-3 rounded-card bg-surface p-4 shadow-card">
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="text-lead font-bold">Лимит месяца</h3>
        <span className="text-body font-semibold">{limitText(paidThisMonth, paidLimitMonth)}</span>
      </div>
      <ProgressBar value={paidThisMonth} max={paidLimitMonth} />
    </section>
  );
}
