import { apiGet, apiPost } from "@/shared/api/client";
import type { paths } from "@/shared/api/schema";

export type ChallengeListResponse =
  paths["/api/v1/users/{user_id}/challenges"]["get"]["responses"]["200"]["content"]["application/json"];
export type ChallengeDetail = NonNullable<ChallengeListResponse["hero"]>;
export type ChallengeHistoryItem = ChallengeListResponse["history"][number];

export function getChallenges(userId: number): Promise<ChallengeListResponse> {
  return apiGet<ChallengeListResponse>(`/api/v1/users/${userId}/challenges`);
}

export function refreshChallenges(userId: number): Promise<ChallengeListResponse> {
  return apiPost<ChallengeListResponse>(`/api/v1/users/${userId}/challenges/refresh`);
}
