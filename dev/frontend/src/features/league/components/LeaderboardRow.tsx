import type { LeagueResponse } from "../api";
import { zoneRowClass, type LeagueZone } from "../format";

type LeagueMember = LeagueResponse["members"][number];

type LeaderboardRowProps = {
  member: LeagueMember;
  zone: LeagueZone;
};

export function LeaderboardRow({ member, zone }: LeaderboardRowProps) {
  return (
    <div
      data-testid="league-row"
      className={`flex items-center justify-between rounded-lg px-3 py-2 ${zoneRowClass(zone)} ${
        member.is_me ? "bg-brand-100 font-semibold text-brand-900" : "bg-surface text-text"
      }`}
    >
      <div className="flex items-center gap-3">
        <span className="w-6 text-sm text-text-secondary">{member.rank}</span>
        <span className="text-sm">{member.pseudonym}</span>
        {member.is_me && (
          <span className="rounded-full bg-brand-600 px-2 py-0.5 text-[10px] font-semibold text-white">
            Вы
          </span>
        )}
      </div>
      <div className="flex items-center gap-3 text-sm text-text-secondary">
        <span>ур. {member.level}</span>
        <span className="font-semibold text-text">{member.score}</span>
      </div>
    </div>
  );
}
