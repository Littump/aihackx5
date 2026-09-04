import { Card } from "@/shared/ui/Card";
import { formatDateTime } from "../format";
import type { PmUserResponse } from "../api";

type LedgerBlockProps = {
  ledger: PmUserResponse["ledger"];
};

export function LedgerBlock({ ledger }: LedgerBlockProps) {
  return (
    <Card className="flex flex-col gap-3">
      <h2 className="text-lead font-bold">Журнал начислений</h2>
      {ledger.length === 0 ? (
        <p className="text-ink-500">Записей пока нет.</p>
      ) : (
        <div className="w-full overflow-x-auto">
          <table className="w-full min-w-[480px] border-collapse text-body">
            <thead>
              <tr className="text-left text-caption text-ink-500">
                <th className="py-2 font-normal">Когда</th>
                <th className="py-2 font-normal">Тип</th>
                <th className="py-2 font-normal">XP</th>
                <th className="py-2 font-normal">Баллы</th>
                <th className="py-2 font-normal">Источник</th>
              </tr>
            </thead>
            <tbody>
              {ledger.map((entry, index) => (
                <tr key={`${entry.created_at}-${index}`} className="border-t border-line">
                  <td className="py-2 text-ink-900">{formatDateTime(entry.created_at)}</td>
                  <td className="py-2 text-ink-900">{entry.kind}</td>
                  <td className="py-2 text-ink-900">{entry.xp_delta}</td>
                  <td className="py-2 text-ink-900">{entry.points_delta}</td>
                  <td className="py-2 text-ink-500">
                    {entry.ref_type ? `${entry.ref_type} #${entry.ref_id}` : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
