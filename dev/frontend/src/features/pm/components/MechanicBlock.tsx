import { Card } from "@/shared/ui/Card";
import { mechanicLabel } from "../format";
import type { PmUserResponse } from "../api";

type MechanicBlockProps = {
  recommendedMechanic: PmUserResponse["recommended_mechanic"];
};

export function MechanicBlock({ recommendedMechanic }: MechanicBlockProps) {
  return (
    <Card>
      <h2 className="text-lg font-semibold text-text">Механика и почему</h2>
      <p className="mt-2 text-sm text-text-secondary">Рекомендованная механика</p>
      <span className="mt-1 inline-block rounded-full bg-brand-100 px-3 py-1 text-sm font-semibold text-brand-600">
        {mechanicLabel(recommendedMechanic.mechanic)}
      </span>
      <p className="mt-3 text-xs font-medium uppercase text-text-secondary">Причины</p>
      <ul className="mt-1 list-disc pl-5 text-sm text-text">
        {recommendedMechanic.reasons.map((reason) => (
          <li key={reason}>{reason}</li>
        ))}
      </ul>
    </Card>
  );
}
