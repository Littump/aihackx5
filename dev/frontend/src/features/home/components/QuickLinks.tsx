import type { ReactNode } from "react";
import { useSearchParams } from "react-router";
import { Tile } from "@/shared/ui/Tile";
import { NAV_ICON_PATHS } from "@/shared/ui/navIcons";
import type { HomeResponse } from "../api";

type QuickLinksProps = {
  league: HomeResponse["league"];
  referral: HomeResponse["referral"];
};

function NavIcon({ children }: { children: ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      className="h-6 w-6"
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

export function QuickLinks({ league, referral }: QuickLinksProps) {
  const [searchParams] = useSearchParams();
  const suffix = `?${searchParams.toString()}`;
  return (
    <div className="grid shrink-0 grid-cols-2 gap-3">
      <Tile
        to={`/league${suffix}`}
        icon={<NavIcon>{NAV_ICON_PATHS.league}</NavIcon>}
        title="Лига"
        subtitle={league ? `Место ${league.rank} из ${league.size}` : "Пока нет лиги"}
      />
      <Tile
        to={`/referral${suffix}`}
        icon={<NavIcon>{NAV_ICON_PATHS.referral}</NavIcon>}
        title="Соседи"
        subtitle={`Приглашено: ${referral.invited_count}`}
      />
    </div>
  );
}
