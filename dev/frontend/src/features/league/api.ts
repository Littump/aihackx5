import { apiGet } from "@/shared/api/client";
import type { paths } from "@/shared/api/schema";

export type LeagueResponse =
  paths["/api/v1/users/{user_id}/league"]["get"]["responses"]["200"]["content"]["application/json"];

export function getLeague(userId: number): Promise<LeagueResponse> {
  return apiGet<LeagueResponse>(`/api/v1/users/${userId}/league`);
}
