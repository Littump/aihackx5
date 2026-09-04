import { Card } from "@/shared/ui/Card";
import { Skeleton } from "@/shared/ui/Skeleton";

export function ReferralSkeleton() {
  return (
    <div className="flex flex-1 flex-col gap-4" aria-busy="true">
      <Card className="flex flex-col gap-4">
        <div className="flex items-center gap-4">
          <Skeleton className="h-24 w-24 shrink-0" />
          <div className="flex flex-1 flex-col gap-2">
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-6 w-2/3" />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Skeleton className="h-11 w-full" />
          <Skeleton className="h-11 w-full" />
        </div>
      </Card>
      <Card className="flex flex-col gap-3">
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
      </Card>
      <Card className="flex flex-col gap-3">
        <Skeleton className="h-4 w-1/4" />
        <Skeleton className="h-3 w-full" />
      </Card>
      <Card className="flex flex-col gap-2 divide-y divide-line p-0">
        <Skeleton className="m-4 h-4 w-full" />
        <Skeleton className="m-4 h-4 w-full" />
        <Skeleton className="m-4 h-4 w-3/4" />
      </Card>
    </div>
  );
}
