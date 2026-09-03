import { useQuery } from "@tanstack/react-query";
import { getReferral } from "./api";

export function useReferral(userId: number | null) {
  return useQuery({
    queryKey: ["referral", userId],
    queryFn: () => getReferral(userId as number),
    enabled: userId !== null,
  });
}
