import { Card } from "@/shared/ui/Card";
import type { LeagueResponse } from "../api";
import { zoneForRank, zoneLabel, type LeagueZone } from "../format";
import { LeaderboardRow } from "./LeaderboardRow";

type LeaderboardListProps = {
  league: LeagueResponse;
};

const LEGEND_ZONES: LeagueZone[] = ["promotion", "safe", "demotion"];

export function LeaderboardList({ league }: LeaderboardListProps) {
  return (
    <Card className="flex flex-col gap-2">
      <h2 className="text-sm font-semibold text-text">Таблица лиги · {league.size} участников</h2>
      <div className="flex gap-3 text-[11px] text-text-secondary">
        {LEGEND_ZONES.map((zone) => (
          <span key={zone}>{zoneLabel(zone)}</span>
        ))}
      </div>
      <div className="flex flex-col gap-1">
        {league.members.map((member) => (
          <LeaderboardRow
            key={member.rank}
            member={member}
            zone={zoneForRank(member.rank, league.promotion_cutoff, league.demotion_cutoff)}
          />
        ))}
      </div>
    </Card>
  );
}
