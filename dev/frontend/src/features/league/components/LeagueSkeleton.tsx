import { Card } from "@/shared/ui/Card";
import { Skeleton } from "@/shared/ui/Skeleton";

const HEADER_TILE_COUNT = 3;
const ROW_COUNT = 6;

export function LeagueSkeleton() {
  return (
    <section className="flex flex-1 flex-col gap-4 px-4 py-4" aria-busy="true">
      <div className="grid shrink-0 grid-cols-3 gap-3">
        {Array.from({ length: HEADER_TILE_COUNT }).map((_, index) => (
          <Skeleton key={index} className="h-16 w-full" />
        ))}
      </div>
      <Card className="flex flex-col gap-2 divide-y divide-line p-0">
        {Array.from({ length: ROW_COUNT }).map((_, index) => (
          <Skeleton key={index} className="m-4 h-6 w-full" />
        ))}
      </Card>
      <Card className="flex flex-col gap-3">
        <Skeleton className="h-4 w-2/3" />
        <div className="grid grid-cols-2 gap-3">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      </Card>
    </section>
  );
}
