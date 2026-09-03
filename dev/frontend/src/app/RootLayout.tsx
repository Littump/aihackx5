import { Outlet } from "react-router";
import { UserProvider } from "@/features/users/UserContext";
import { UserSwitcher } from "@/features/users/UserSwitcher";
import { PhoneShell } from "@/shared/ui/PhoneShell";
import { BottomNav } from "@/shared/ui/BottomNav";

export function RootLayout() {
  return (
    <UserProvider>
      <PhoneShell header={<UserSwitcher />} footer={<BottomNav />}>
        <Outlet />
      </PhoneShell>
    </UserProvider>
  );
}
