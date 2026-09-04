import { NavLink, useSearchParams } from "react-router";
import { NAV_ICON_PATHS, type NavIconKey } from "./navIcons";

type NavItem = {
  to: string;
  label: string;
  key: NavIconKey;
};

const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Дом", key: "home" },
  { to: "/challenge", label: "Цель", key: "goal" },
  { to: "/league", label: "Лига", key: "league" },
  { to: "/referral", label: "Соседи", key: "referral" },
];

export function BottomNav() {
  const [searchParams] = useSearchParams();
  const search = searchParams.toString();
  return (
    <nav
      className="grid shrink-0 grid-cols-4 bg-surface px-2 pt-2 pb-3 shadow-nav"
      aria-label="Основная навигация"
    >
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={{ pathname: item.to, search }}
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
            {NAV_ICON_PATHS[item.key]}
          </svg>
          <span className="text-caption">{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
