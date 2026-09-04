import { useQuery } from "@tanstack/react-query";
import { getRewards } from "./api";

export function useRewards(userId: number | null) {
  return useQuery({
    queryKey: ["rewards", userId],
    queryFn: () => getRewards(userId as number),
    enabled: userId !== null,
  });
}
