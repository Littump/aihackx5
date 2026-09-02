import type { LeagueResponse } from "./types";
import { USERS } from "./users";

export function getLeague(userId: number): LeagueResponse {
  const members = USERS.map((user, index) => ({
    pseudonym: user.pseudonym,
    level: user.level,
    score: 160 - index * 18,
    rank: index + 1,
    is_me: user.id === userId,
  }));
  const me = members.find((member) => member.is_me);
  return {
    division: 2,
    division_name: "серебро",
    week_start: "2026-08-31",
    week_end: "2026-09-06",
    size: members.length,
    my_rank: me?.rank ?? 1,
    my_score: me?.score ?? 124,
    my_zone: "safe",
    promotion_cutoff: 7,
    demotion_cutoff: 5,
    members,
    house: {
      store_name: "Пятёрочка на Ленина",
      avg_savings_rate: 0.12,
      district_rank: 3,
      district_size: 12,
    },
  };
}
