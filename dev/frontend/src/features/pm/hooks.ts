import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { ApiError } from "@/shared/api/client";
import { getFraudChecks, getLatestEval, getLatestSimulation, getPmUser } from "./api";
import type { FraudDecision } from "./api";

export function usePmUser(userId: number | null) {
  return useQuery({
    queryKey: ["pm-user", userId],
    queryFn: () => getPmUser(userId as number),
    enabled: userId !== null,
  });
}

export function usePmFraudChecks(decision: FraudDecision | null) {
  return useQuery({
    queryKey: ["pm-fraud", decision],
    queryFn: () => getFraudChecks(decision),
  });
}

export function usePmSimulation() {
  return useQuery({ queryKey: ["pm-simulation"], queryFn: getLatestSimulation, retry: false });
}

export function usePmEval() {
  return useQuery({ queryKey: ["pm-eval"], queryFn: getLatestEval, retry: false });
}

export function isNotFoundError(query: UseQueryResult<unknown, Error>): boolean {
  return query.isError && query.error instanceof ApiError && query.error.status === 404;
}
