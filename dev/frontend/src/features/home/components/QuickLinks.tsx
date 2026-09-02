import { Link, useSearchParams } from "react-router";
import { Card } from "@/shared/ui/Card";
import type { HomeResponse } from "../api";

type QuickLinksProps = {
  league: HomeResponse["league"];
  referral: HomeResponse["referral"];
};

export function QuickLinks({ league, referral }: QuickLinksProps) {
  const [searchParams] = useSearchParams();
  const suffix = `?${searchParams.toString()}`;
  return (
    <div className="grid grid-cols-2 gap-3">
      <Link to={`/league${suffix}`}>
        <Card className="h-full">
          <p className="text-xs text-text-secondary">Лига</p>
          <p className="text-sm font-medium text-text">
            {league ? `Место ${league.rank} из ${league.size}` : "Пока нет лиги"}
          </p>
        </Card>
      </Link>
      <Link to={`/referral${suffix}`}>
        <Card className="h-full">
          <p className="text-xs text-text-secondary">Соседи</p>
          <p className="text-sm font-medium text-text">Приглашено: {referral.invited_count}</p>
        </Card>
      </Link>
    </div>
  );
}
