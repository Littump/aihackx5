import type { ReactNode } from "react";
import { NavLink } from "react-router";

type NavKey = "home" | "goal" | "league" | "referral";

type NavItem = {
  to: string;
  label: string;
  key: NavKey;
};

const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Дом", key: "home" },
  { to: "/challenge", label: "Цель", key: "goal" },
  { to: "/league", label: "Лига", key: "league" },
  { to: "/referral", label: "Соседи", key: "referral" },
];

const NAV_ICONS: Record<NavKey, ReactNode> = {
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

export function BottomNav() {
  return (
    <nav
      className="grid shrink-0 grid-cols-4 bg-surface px-2 pt-2 pb-3 shadow-nav"
      aria-label="Основная навигация"
    >
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === "/"}
          className={({ isActive }) =>
            `flex flex-col items-center gap-1 py-2 ${
              isActive ? "font-semibold text-brand-600" : "text-ink-500"
            }`
          }
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
            className="h-6 w-6"
            aria-hidden="true"
          >
            {NAV_ICONS[item.key]}
          </svg>
          <span className="text-caption">{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
