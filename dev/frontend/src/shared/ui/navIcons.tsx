import type { ReactNode } from "react";

export type NavIconKey = "home" | "goal" | "league" | "referral";

export const NAV_ICON_PATHS: Record<NavIconKey, ReactNode> = {
  home: (
    <>
      <path d="m3 11 9-7 9 7v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z" />
      <path d="M10 21v-6h4v6" />
    </>
  ),
  goal: (
    <>
      <circle cx="12" cy="12" r="8" />
      <circle cx="12" cy="12" r="3" />
    </>
  ),
  league: <path d="M8 4h8v5a4 4 0 0 1-8 0zM12 13v4M9 21h6" />,
  referral: (
    <>
      <circle cx="9" cy="8" r="3" />
      <path d="M3 20a6 6 0 0 1 12 0M17 11h4M19 9v4" />
    </>
  ),
};
