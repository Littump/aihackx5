import { useId, useState, type ReactNode } from "react";

type InfoHintProps = {
  label: string;
  children: ReactNode;
  className?: string;
};

export function InfoHint({ label, children, className = "" }: InfoHintProps) {
  const [open, setOpen] = useState(false);
  const tooltipId = useId();

  return (
    <span
      className={`relative inline-flex ${className}`}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        aria-label={label}
        aria-describedby={open ? tooltipId : undefined}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-50 text-caption font-bold text-brand-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-700"
      >
        ?
      </button>
      {open && (
        <span
          id={tooltipId}
          role="tooltip"
          className="absolute right-0 top-8 z-20 block w-64 rounded-tile bg-ink-900 p-3 text-caption text-pretty text-white shadow-card"
        >
          <span
            aria-hidden="true"
            className="absolute right-2 -top-1 block h-3 w-3 rotate-45 rounded-[2px] bg-ink-900"
          />
          {children}
        </span>
      )}
    </span>
  );
}
