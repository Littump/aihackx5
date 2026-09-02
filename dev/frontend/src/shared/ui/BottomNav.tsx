import { NavLink } from "react-router";

type NavItem = {
  to: string;
  label: string;
  icon: string;
};

const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Дом", icon: "\u{1F3E0}" },
  { to: "/challenge", label: "Челлендж", icon: "\u{1F3AF}" },
  { to: "/league", label: "Лига", icon: "\u{1F3C6}" },
  { to: "/referral", label: "Соседи", icon: "\u{1F91D}" },
];

export function BottomNav() {
  return (
    <nav className="flex border-t border-border bg-surface" aria-label="Основная навигация">
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === "/"}
          className={({ isActive }) =>
            `flex flex-1 flex-col items-center gap-1 py-2 text-xs ${
              isActive ? "font-semibold text-brand-900" : "text-text-secondary"
            }`
          }
        >
          <span aria-hidden="true" className="text-lg">
            {item.icon}
          </span>
          <span>{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
