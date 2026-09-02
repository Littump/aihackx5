import type { ReactNode } from "react";

type PhoneShellProps = {
  header?: ReactNode;
  children: ReactNode;
};

export function PhoneShell({ header, children }: PhoneShellProps) {
  return (
    <div className="flex min-h-screen justify-center bg-bg">
      <div className="flex min-h-screen w-full max-w-[430px] flex-col bg-surface shadow-lg">
        {header}
        <div className="flex flex-1 flex-col overflow-y-auto">{children}</div>
      </div>
    </div>
  );
}
