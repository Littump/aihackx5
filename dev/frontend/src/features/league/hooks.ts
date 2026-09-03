import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { leagueRankChangeKey } from "@/shared/lib/queryKeys";
import { getLeague } from "./api";

export function useLeague(userId: number | null) {
  return useQuery({
    queryKey: ["league", userId],
    queryFn: () => getLeague(userId as number),
    enabled: userId !== null,
  });
}

export type LeagueRankChange = {
  before: number | null;
  after: number | null;
};

export function useLeagueRankChange(userId: number | null): LeagueRankChange | null {
  const queryClient = useQueryClient();
  const [change, setChange] = useState<LeagueRankChange | null>(null);

  useEffect(() => {
    const key = leagueRankChangeKey(userId);
    const cached = queryClient.getQueryData<LeagueRankChange>(key);
    if (cached === undefined) return;
    setChange(cached);
    queryClient.removeQueries({ queryKey: key });
  }, [userId, queryClient]);

  return change;
}
