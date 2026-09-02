import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getHome, simulateReceipt } from "./api";

export function useHome(userId: number | null) {
  return useQuery({
    queryKey: ["home", userId],
    queryFn: () => getHome(userId as number),
    enabled: userId !== null,
  });
}

export function useSimulateReceipt(userId: number | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => simulateReceipt(userId as number),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["home", userId] });
      queryClient.invalidateQueries({ queryKey: ["challenges", userId] });
      queryClient.invalidateQueries({ queryKey: ["league", userId] });
    },
  });
}
