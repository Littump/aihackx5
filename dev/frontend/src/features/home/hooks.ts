import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { leagueRankChangeKey } from "@/shared/lib/queryKeys";
import { getHome, getSimulateDraft, simulateReceipt, type SimulateItemInput } from "./api";

export function useHome(userId: number | null) {
  return useQuery({
    queryKey: ["home", userId],
    queryFn: () => getHome(userId as number),
    enabled: userId !== null,
  });
}

export function useSimulateDraft(userId: number | null, enabled: boolean) {
  return useQuery({
    queryKey: ["simulate-draft", userId],
    queryFn: () => getSimulateDraft(userId as number),
    enabled: enabled && userId !== null,
    gcTime: 0,
    staleTime: 0,
  });
}

export function useSimulateReceipt(userId: number | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (items: SimulateItemInput[]) => simulateReceipt(userId as number, items),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["home", userId] });
      queryClient.invalidateQueries({ queryKey: ["challenges", userId] });
      queryClient.invalidateQueries({ queryKey: ["league", userId] });
      queryClient.setQueryData(leagueRankChangeKey(userId), {
        before: data.league_rank_before,
        after: data.league_rank_after,
      });
    },
  });
}
