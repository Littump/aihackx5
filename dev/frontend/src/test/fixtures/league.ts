import { LEAGUE_DEMOTE_BOTTOM, LEAGUE_PROMOTE_TOP } from "./game_rules";
import type { LeagueResponse } from "./types";
import { getUserSummary } from "./users";

const LEAGUE_SIZE = 24;

const MY_RANK_BY_USER: Record<number, number> = {
  1: 3,
  2: 12,
  3: 22,
};

function promotionCutoff(size: number): number {
  return Math.min(LEAGUE_PROMOTE_TOP, size);
}

function demotionCutoff(size: number): number {
  return Math.max(size - LEAGUE_DEMOTE_BOTTOM + 1, promotionCutoff(size) + 1);
}

function fillerPseudonym(rank: number): string {
  return `Сосед-Бережливый-${rank}`;
}

function fillerLevel(rank: number): number {
  return Math.max(1, 6 - Math.floor(rank / 5));
}

function scoreForRank(rank: number): number {
  return 210 - rank * 6;
}

export function getLeague(userId: number): LeagueResponse {
  const myRank = MY_RANK_BY_USER[userId] ?? MY_RANK_BY_USER[1];
  const myUser = getUserSummary(userId);
  const members = Array.from({ length: LEAGUE_SIZE }, (_, index) => {
    const rank = index + 1;
    const isMe = rank === myRank;
    return {
      pseudonym: isMe ? myUser.pseudonym : fillerPseudonym(rank),
      level: isMe ? myUser.level : fillerLevel(rank),
      score: scoreForRank(rank),
      rank,
      is_me: isMe,
    };
  });
  const me = members.find((member) => member.is_me);
  if (me === undefined) throw new Error(`league fixture: no member at rank ${myRank}`);
  const promotion_cutoff = promotionCutoff(LEAGUE_SIZE);
  const demotion_cutoff = demotionCutoff(LEAGUE_SIZE);
  const my_zone =
    me.rank <= promotion_cutoff ? "promotion" : me.rank >= demotion_cutoff ? "demotion" : "safe";
  return {
    division: 2,
    division_name: "серебро",
    week_start: "2026-08-31",
    week_end: "2026-09-06",
    size: members.length,
    my_rank: me.rank,
    my_score: me.score,
    my_zone,
    promotion_cutoff,
    demotion_cutoff,
    members,
    house: {
      store_name: "Пятёрочка на Ленина",
      avg_savings_rate: 0.12,
      district_rank: 3,
      district_size: 12,
    },
  };
}
