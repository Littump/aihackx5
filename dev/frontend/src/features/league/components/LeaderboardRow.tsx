import type { LeagueResponse } from "../api";
import { zoneLabel, zoneRowClass, type LeagueZone } from "../format";

type LeagueMember = LeagueResponse["members"][number];

type LeaderboardRowProps = {
  member: LeagueMember;
  zone: LeagueZone;
};

export function LeaderboardRow({ member, zone }: LeaderboardRowProps) {
  if (member.is_me) {
    return (
      <div
        data-testid="league-row"
        className="flex items-center gap-3 bg-brand-700 px-4 py-3 text-white"
      >
        <span className="w-8 text-body font-bold">{member.rank}</span>
        <span className="flex flex-1 flex-col">
          <span className="text-body font-semibold">Вы</span>
          <span className="text-caption text-brand-100">
            уровень {member.level} · зона {zoneLabel(zone).toLowerCase()}
          </span>
        </span>
        <span className="text-body font-bold">{member.score}</span>
      </div>
    );
  }

  return (
    <div
      data-testid="league-row"
      className={`flex items-center gap-3 px-4 py-3 ${zoneRowClass(zone)}`}
    >
      <span className="w-8 text-body font-bold">{member.rank}</span>
      <span className="flex flex-1 flex-col">
        <span className="text-body">{member.pseudonym}</span>
        <span className="text-caption text-ink-500">уровень {member.level}</span>
      </span>
      <span className="text-body font-semibold">{member.score}</span>
    </div>
  );
}
