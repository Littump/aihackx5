import { apiGet, apiPost } from "@/shared/api/client";
import type { components, paths } from "@/shared/api/schema";

export type HomeResponse =
  paths["/api/v1/users/{user_id}/home"]["get"]["responses"]["200"]["content"]["application/json"];

export type ReceiptProcessingResult =
  paths["/api/v1/users/{user_id}/receipts/simulate"]["post"]["responses"]["201"]["content"]["application/json"];

export type SimulateDraft = components["schemas"]["SimulateDraft"];
export type SimulateDraftItem = components["schemas"]["SimulateDraftItem"];
export type SimulateItemInput = components["schemas"]["SimulateItemInput"];

export function getHome(userId: number): Promise<HomeResponse> {
  return apiGet<HomeResponse>(`/api/v1/users/${userId}/home`);
}

export function getSimulateDraft(userId: number): Promise<SimulateDraft> {
  return apiGet<SimulateDraft>(`/api/v1/users/${userId}/receipts/simulate/draft`);
}

export function simulateReceipt(
  userId: number,
  items?: SimulateItemInput[],
): Promise<ReceiptProcessingResult> {
  const body = items === undefined ? undefined : { items };
  return apiPost<ReceiptProcessingResult>(`/api/v1/users/${userId}/receipts/simulate`, body);
}
