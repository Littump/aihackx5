import { Card } from "@/shared/ui/Card";
import { formatDateTime } from "../format";
import type { PmUserResponse } from "../api";

type LedgerBlockProps = {
  ledger: PmUserResponse["ledger"];
};

export function LedgerBlock({ ledger }: LedgerBlockProps) {
  return (
    <Card>
      <h2 className="text-lg font-semibold text-text">Ledger</h2>
      {ledger.length === 0 ? (
        <p className="mt-2 text-text-secondary">Записей пока нет.</p>
      ) : (
        <table className="mt-3 w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-text-secondary">
              <th className="pb-1 font-normal">Когда</th>
              <th className="pb-1 font-normal">Тип</th>
              <th className="pb-1 font-normal">XP</th>
              <th className="pb-1 font-normal">Баллы</th>
              <th className="pb-1 font-normal">Источник</th>
            </tr>
          </thead>
          <tbody>
            {ledger.map((entry, index) => (
              <tr key={`${entry.created_at}-${index}`} className="border-t border-border">
                <td className="py-1 text-text">{formatDateTime(entry.created_at)}</td>
                <td className="py-1 text-text">{entry.kind}</td>
                <td className="py-1 text-text">{entry.xp_delta}</td>
                <td className="py-1 text-text">{entry.points_delta}</td>
                <td className="py-1 text-text-secondary">
                  {entry.ref_type ? `${entry.ref_type} #${entry.ref_id}` : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Card>
  );
}
