import { Outlet } from "react-router";
import { UserProvider } from "@/features/users/UserContext";
import { UserSwitcher } from "@/features/users/UserSwitcher";

export function PmLayout() {
  return (
    <UserProvider>
      <div className="min-h-screen bg-bg">
        <UserSwitcher />
        <div className="mx-auto max-w-6xl px-6 py-6">
          <Outlet />
        </div>
      </div>
    </UserProvider>
  );
}
