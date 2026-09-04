import { Card } from "@/shared/ui/Card";
import { Skeleton } from "@/shared/ui/Skeleton";

export function ChallengeSkeleton() {
  return (
    <div className="flex flex-1 flex-col gap-4" aria-busy="true">
      <Card className="flex flex-col gap-3">
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-6 w-2/3" />
        <Skeleton className="h-4 w-full" />
        <div className="grid grid-cols-2 gap-3">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-10 w-1/2" />
      </Card>
      <Card className="flex flex-col gap-3">
        <Skeleton className="h-4 w-2/3" />
        <Skeleton className="h-2 w-full" />
        <Skeleton className="h-4 w-1/2" />
      </Card>
      <Card className="flex flex-col gap-2 divide-y divide-line p-0">
        <Skeleton className="m-4 h-4 w-full" />
        <Skeleton className="m-4 h-4 w-full" />
        <Skeleton className="m-4 h-4 w-3/4" />
      </Card>
    </div>
  );
}
