import { Outlet } from "react-router";
import { BottomNav } from "@/shared/ui/BottomNav";

export function ConsumerLayout() {
  return (
    <div className="flex flex-1 flex-col">
      <div className="flex flex-1 flex-col">
        <Outlet />
      </div>
      <BottomNav />
    </div>
  );
}
