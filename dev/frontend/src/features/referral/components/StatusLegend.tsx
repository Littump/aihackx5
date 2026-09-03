import type { ReferralStatus } from "../format";
import { statusIconShape, statusText, statusToneClasses } from "../format";
import { StatusIcon } from "./StatusIcon";

const LEGEND_STATUSES: ReferralStatus[] = [
  "pending",
  "first_purchase",
  "qualified",
  "on_review",
  "rewarded",
  "blocked",
];

export function StatusLegend() {
  return (
    <section className="flex shrink-0 flex-col gap-3 rounded-card bg-surface p-4 shadow-card">
      <h3 className="text-lead font-bold">Как читать статусы</h3>
      <ul className="m-0 flex list-none flex-col gap-2 pl-0">
        {LEGEND_STATUSES.map((status) => (
          <li key={status} className="flex items-center gap-2 text-body">
            <span
              className={`flex h-8 w-8 items-center justify-center rounded-tile ${statusToneClasses(status)}`}
            >
              <StatusIcon shapes={statusIconShape(status)} />
            </span>
            {statusText(status)}
          </li>
        ))}
      </ul>
    </section>
  );
}
