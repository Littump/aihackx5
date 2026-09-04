import { apiGet } from "@/shared/api/client";
import type { components, paths } from "@/shared/api/schema";

export type RewardsResponse =
  paths["/api/v1/users/{user_id}/rewards"]["get"]["responses"]["200"]["content"]["application/json"];

export type RewardEvent = components["schemas"]["RewardEvent"];
export type RewardRule = components["schemas"]["RewardRule"];

export function getRewards(userId: number): Promise<RewardsResponse> {
  return apiGet<RewardsResponse>(`/api/v1/users/${userId}/rewards`);
}
