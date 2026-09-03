import { apiGet } from "@/shared/api/client";
import type { paths } from "@/shared/api/schema";

export type PmUserResponse =
  paths["/api/v1/pm/users/{user_id}"]["get"]["responses"]["200"]["content"]["application/json"];
export type FraudCheckListResponse =
  paths["/api/v1/pm/fraud"]["get"]["responses"]["200"]["content"]["application/json"];
export type FraudCheck = FraudCheckListResponse["items"][number];
export type FraudDecision = FraudCheck["decision"];
export type SimulationRun =
  paths["/api/v1/pm/simulation/latest"]["get"]["responses"]["200"]["content"]["application/json"];
export type EvalRun =
  paths["/api/v1/pm/eval/latest"]["get"]["responses"]["200"]["content"]["application/json"];

export function getPmUser(userId: number): Promise<PmUserResponse> {
  return apiGet<PmUserResponse>(`/api/v1/pm/users/${userId}`);
}

export function getFraudChecks(decision: FraudDecision | null): Promise<FraudCheckListResponse> {
  const query = decision ? `?decision=${decision}` : "";
  return apiGet<FraudCheckListResponse>(`/api/v1/pm/fraud${query}`);
}

export function getLatestSimulation(): Promise<SimulationRun> {
  return apiGet<SimulationRun>("/api/v1/pm/simulation/latest");
}

export function getLatestEval(): Promise<EvalRun> {
  return apiGet<EvalRun>("/api/v1/pm/eval/latest");
}
