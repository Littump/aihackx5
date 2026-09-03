import { Outlet } from "react-router";
import { UserProvider } from "@/features/users/UserContext";
import { UserSwitcher } from "@/features/users/UserSwitcher";

export function PmLayout() {
  return (
    <UserProvider>
      <div className="min-h-dvh bg-desk">
        <UserSwitcher />
        <section className="mx-auto max-w-pm px-6 py-6">
          <div className="rounded-sheet bg-canvas p-6 shadow-lift">
            <Outlet />
          </div>
        </section>
      </div>
    </UserProvider>
  );
}
