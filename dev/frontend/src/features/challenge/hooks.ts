import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getChallenges, refreshChallenges } from "./api";

export function useChallenges(userId: number | null) {
  return useQuery({
    queryKey: ["challenges", userId],
    queryFn: () => getChallenges(userId as number),
    enabled: userId !== null,
  });
}

export function useRefreshChallenges(userId: number | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => refreshChallenges(userId as number),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["challenges", userId] });
    },
  });
}
