import type { ReactNode } from "react";

type PhoneShellProps = {
  header?: ReactNode;
  footer?: ReactNode;
  children: ReactNode;
};

export function PhoneShell({ header, footer, children }: PhoneShellProps) {
  return (
    <div className="flex min-h-dvh justify-center bg-desk">
      <div className="flex w-full max-w-[430px] flex-col overflow-hidden rounded-sheet bg-canvas shadow-lift">
        {header}
        <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
        {footer}
      </div>
    </div>
  );
}
