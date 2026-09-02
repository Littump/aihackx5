import { Outlet } from "react-router";
import { UserProvider } from "@/features/users/UserContext";
import { UserSwitcher } from "@/features/users/UserSwitcher";
import { PhoneShell } from "@/shared/ui/PhoneShell";

export function RootLayout() {
  return (
    <UserProvider>
      <PhoneShell header={<UserSwitcher />}>
        <Outlet />
      </PhoneShell>
    </UserProvider>
  );
}
