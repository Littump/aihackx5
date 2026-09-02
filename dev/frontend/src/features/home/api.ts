import { apiGet, apiPost } from "@/shared/api/client";
import type { paths } from "@/shared/api/schema";

export type HomeResponse =
  paths["/api/v1/users/{user_id}/home"]["get"]["responses"]["200"]["content"]["application/json"];

export type ReceiptProcessingResult =
  paths["/api/v1/users/{user_id}/receipts/simulate"]["post"]["responses"]["201"]["content"]["application/json"];

export function getHome(userId: number): Promise<HomeResponse> {
  return apiGet<HomeResponse>(`/api/v1/users/${userId}/home`);
}

export function simulateReceipt(userId: number): Promise<ReceiptProcessingResult> {
  return apiPost<ReceiptProcessingResult>(`/api/v1/users/${userId}/receipts/simulate`);
}
