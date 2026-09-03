import type { ReactNode } from "react";

type StatusChipStatus = "success" | "inProgress" | "failed" | "neutral";

type StatusChipProps = {
  status: StatusChipStatus;
  label: string;
  className?: string;
};

type StatusConfig = {
  classes: string;
  icon: ReactNode;
};

const STATUS_CONFIG: Record<StatusChipStatus, StatusConfig> = {
  success: {
    classes: "bg-brand-50 text-brand-700",
    icon: <path d="m4 13 5 5L20 7" />,
  },
  inProgress: {
    classes: "bg-accent-50 text-accent-700",
    icon: (
      <>
        <circle cx="12" cy="12" r="8" />
        <path d="M12 8v4l3 2" />
      </>
    ),
  },
  failed: {
    classes: "bg-canvas text-ink-700",
    icon: <path d="M6 6l12 12M18 6 6 18" />,
  },
  neutral: {
    classes: "bg-canvas text-ink-500",
    icon: (
      <>
        <circle cx="11" cy="11" r="6" />
        <path d="m16 16 4 4" />
      </>
    ),
  },
};

export function StatusChip({ status, label, className = "" }: StatusChipProps) {
  const config = STATUS_CONFIG[status];
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-tile px-3 py-1 text-caption font-semibold ${config.classes} ${className}`}
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        className="h-6 w-6 shrink-0"
        aria-hidden="true"
      >
        {config.icon}
      </svg>
      {label}
    </span>
  );
}
