import { apiGet } from "@/shared/api/client";
import type { paths } from "@/shared/api/schema";

export type ReferralResponse =
  paths["/api/v1/users/{user_id}/referral"]["get"]["responses"]["200"]["content"]["application/json"];

export function getReferral(userId: number): Promise<ReferralResponse> {
  return apiGet<ReferralResponse>(`/api/v1/users/${userId}/referral`);
}
