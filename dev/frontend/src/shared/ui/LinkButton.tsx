import type { ReactNode } from "react";
import { Link } from "react-router";

type LinkButtonVariant = "primary" | "secondary";

type LinkButtonProps = {
  to: string;
  variant?: LinkButtonVariant;
  className?: string;
  children: ReactNode;
};

const BASE_CLASSES =
  "w-full rounded-tile px-4 py-3 text-center font-semibold no-underline transition-colors " +
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-700";

const VARIANT_CLASSES: Record<LinkButtonVariant, string> = {
  primary: "bg-brand-700 text-white text-lead hover:bg-brand-800 active:bg-brand-800",
  secondary:
    "bg-surface text-brand-700 border border-brand-600 text-body hover:bg-brand-50 active:bg-brand-100",
};

export function LinkButton({ to, variant = "primary", className = "", children }: LinkButtonProps) {
  return (
    <Link to={to} className={`${BASE_CLASSES} ${VARIANT_CLASSES[variant]} ${className}`}>
      {children}
    </Link>
  );
}
