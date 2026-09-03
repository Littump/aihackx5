export function leagueRankChangeKey(userId: number | null) {
  return ["league-rank-change", userId] as const;
}
