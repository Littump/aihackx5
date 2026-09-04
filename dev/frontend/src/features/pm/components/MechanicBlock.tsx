import { Card } from "@/shared/ui/Card";
import type { PmUserResponse } from "../api";

type MechanicBlockProps = {
  recommendedMechanic: PmUserResponse["recommended_mechanic"];
};

export function MechanicBlock({ recommendedMechanic }: MechanicBlockProps) {
  return (
    <Card className="flex flex-col gap-3">
      <h2 className="text-lead font-bold">Механика и обоснование</h2>
      <span className="self-start rounded-tile bg-brand-50 px-3 py-1 font-mono text-caption font-semibold text-brand-700">
        {recommendedMechanic.mechanic}
      </span>
      <ul className="m-0 flex list-none flex-col gap-2 pl-0">
        {recommendedMechanic.reasons.map((reason, index) => (
          <li key={reason} className="flex gap-2 text-body text-ink-700">
            <span className="font-bold text-brand-700">{index + 1}.</span>
            {reason}
          </li>
        ))}
      </ul>
    </Card>
  );
}
