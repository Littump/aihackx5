import { Outlet } from "react-router";

export function ConsumerLayout() {
  return (
    <div className="flex flex-col">
      <Outlet />
    </div>
  );
}
