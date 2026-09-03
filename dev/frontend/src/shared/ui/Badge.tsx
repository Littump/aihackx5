import type { ReactNode } from "react";

type BadgeTone = "accent" | "accentStrong" | "brand";

type BadgeProps = {
  children: ReactNode;
  tone?: BadgeTone;
  className?: string;
};

const TONE_CLASSES: Record<BadgeTone, string> = {
  accent: "bg-accent-50 text-accent-700 text-caption font-semibold",
  accentStrong: "bg-accent-500 text-white text-lead font-bold",
  brand: "bg-brand-50 text-brand-700 text-caption font-semibold",
};

export function Badge({ children, tone = "accent", className = "" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center whitespace-nowrap rounded-tile px-3 py-1 ${TONE_CLASSES[tone]} ${className}`}
    >
      {children}
    </span>
  );
}
