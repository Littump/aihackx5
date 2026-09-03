import { Card } from "@/shared/ui/Card";
import type { LeagueResponse } from "../api";
import { formatPercent } from "../format";

type HouseVsDistrictCardProps = {
  house: LeagueResponse["house"];
};

export function HouseVsDistrictCard({ house }: HouseVsDistrictCardProps) {
  return (
    <Card>
      <p className="text-xs font-medium uppercase text-text-secondary">Дом vs район</p>
      <p className="mt-1 text-sm font-semibold text-text">{house.store_name}</p>
      <p className="mt-2 text-sm text-text">
        Средняя экономия дома:{" "}
        <span className="font-semibold">{formatPercent(house.avg_savings_rate)}</span>
      </p>
      <p className="mt-1 text-sm text-text-secondary">
        Место среди домов района: {house.district_rank} из {house.district_size}
      </p>
    </Card>
  );
}
