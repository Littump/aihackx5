import { Card } from "@/shared/ui/Card";
import { Skeleton } from "@/shared/ui/Skeleton";

export function HomeSkeleton() {
  return (
    <section className="flex flex-1 flex-col gap-3 px-4 py-3" aria-busy="true">
      <Card className="flex flex-col gap-3">
        <div className="flex items-center gap-4">
          <Skeleton className="h-20 w-20 shrink-0" />
          <div className="flex flex-1 flex-col gap-2">
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-4 w-full" />
          </div>
        </div>
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-10 w-1/2" />
      </Card>
      <Card className="flex flex-col gap-3">
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-10 w-2/3" />
        <Skeleton className="h-4 w-1/2" />
      </Card>
      <Card className="flex flex-col gap-3">
        <Skeleton className="h-4 w-1/4" />
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-12 w-full" />
      </Card>
      <div className="grid grid-cols-2 gap-3">
        <Card className="flex flex-col gap-2">
          <Skeleton className="h-6 w-6" />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-1/2" />
        </Card>
        <Card className="flex flex-col gap-2">
          <Skeleton className="h-6 w-6" />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-1/2" />
        </Card>
      </div>
    </section>
  );
}
