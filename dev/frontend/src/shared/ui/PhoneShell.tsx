import { Outlet } from "react-router";

export function PhoneShell() {
  return (
    <div className="flex min-h-screen justify-center bg-gray-100">
      <main className="flex min-h-screen w-full max-w-[430px] flex-col bg-white shadow-lg">
        <Outlet />
      </main>
    </div>
  );
}
