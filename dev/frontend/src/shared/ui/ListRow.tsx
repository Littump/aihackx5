import type { ReactNode } from "react";

type ListRowProps = {
  icon?: ReactNode;
  title: string;
  subtitle?: string;
  value?: ReactNode;
  highlighted?: boolean;
  onClick?: () => void;
  className?: string;
};

const INTERACTIVE_CLASSES =
  "w-full text-left hover:bg-brand-50 active:bg-brand-100 " +
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-700";

export function ListRow({
  icon,
  title,
  subtitle,
  value,
  highlighted = false,
  onClick,
  className = "",
}: ListRowProps) {
  const toneClasses = highlighted ? "bg-brand-700 text-white" : "bg-surface text-ink-900";
  const iconClasses = highlighted ? "bg-brand-800 text-white" : "bg-brand-50 text-brand-700";
  const subtitleClasses = highlighted ? "text-brand-100" : "text-ink-500";

  const content = (
    <>
      {icon && (
        <span
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-tile ${iconClasses}`}
        >
          {icon}
        </span>
      )}
      <span className="flex min-w-0 flex-1 flex-col">
        <span className="text-body font-semibold leading-tight">{title}</span>
        {subtitle && <span className={`text-caption ${subtitleClasses}`}>{subtitle}</span>}
      </span>
      {value !== undefined && <span className="shrink-0 text-body font-semibold">{value}</span>}
    </>
  );

  if (onClick) {
    return (
      <button
        type="button"
        onClick={onClick}
        className={`flex items-center gap-3 p-4 ${toneClasses} ${INTERACTIVE_CLASSES} ${className}`}
      >
        {content}
      </button>
    );
  }

  return <div className={`flex items-center gap-3 p-4 ${toneClasses} ${className}`}>{content}</div>;
}
