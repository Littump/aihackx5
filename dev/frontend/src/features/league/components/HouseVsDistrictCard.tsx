import type { LeagueResponse } from "../api";
import { formatPercent } from "../format";

type HouseVsDistrictCardProps = {
  house: LeagueResponse["house"];
};

export function HouseVsDistrictCard({ house }: HouseVsDistrictCardProps) {
  return (
    <section className="flex shrink-0 flex-col gap-3 rounded-card bg-surface p-4 shadow-card">
      <h3 className="text-lead font-bold leading-tight">Ваш дом против района</h3>
      <p className="text-body text-ink-700">{house.store_name}</p>
      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1 rounded-tile bg-brand-50 p-3">
          <span className="text-caption text-ink-500">Средняя экономия</span>
          <span className="text-title font-bold text-brand-700">
            {formatPercent(house.avg_savings_rate)}
          </span>
        </div>
        <div className="flex flex-col gap-1 rounded-tile bg-brand-50 p-3">
          <span className="text-caption text-ink-500">Место в районе</span>
          <span className="text-title font-bold text-brand-700">
            {house.district_rank} из {house.district_size}
          </span>
        </div>
      </div>
    </section>
  );
}
