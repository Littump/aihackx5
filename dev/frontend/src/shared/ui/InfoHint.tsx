import { useId, useState, type ReactNode } from "react";

type InfoHintProps = {
  label: string;
  children: ReactNode;
  className?: string;
};

export function InfoHint({ label, children, className = "" }: InfoHintProps) {
  const [open, setOpen] = useState(false);
  const panelId = useId();

  return (
    <span className={`inline-flex flex-col items-start ${className}`}>
      <button
        type="button"
        aria-label={label}
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((value) => !value)}
        className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-50 text-caption font-bold text-brand-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-700"
      >
        ?
      </button>
      {open && (
        <span
          id={panelId}
          role="note"
          className="mt-2 block rounded-tile bg-brand-50 p-3 text-caption text-pretty text-ink-700"
        >
          {children}
        </span>
      )}
    </span>
  );
}
