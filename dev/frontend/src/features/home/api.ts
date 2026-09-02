import { apiGet } from "@/shared/api/client";
import type { paths } from "@/shared/api/schema";

export type HealthResponse =
  paths["/api/v1/health"]["get"]["responses"]["200"]["content"]["application/json"];

export function getHealth(): Promise<HealthResponse> {
  return apiGet<HealthResponse>("/api/v1/health");
}
