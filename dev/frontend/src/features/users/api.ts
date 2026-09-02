import { apiGet } from "@/shared/api/client";
import type { paths } from "@/shared/api/schema";

export type UserListResponse =
  paths["/api/v1/users"]["get"]["responses"]["200"]["content"]["application/json"];
export type UserSummary = UserListResponse["items"][number];

export function getUsers(): Promise<UserListResponse> {
  return apiGet<UserListResponse>("/api/v1/users");
}
