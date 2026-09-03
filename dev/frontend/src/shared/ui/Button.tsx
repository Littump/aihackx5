import type { ButtonHTMLAttributes } from "react";

type ButtonVariant = "primary" | "secondary" | "accent" | "link";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
};

const BASE_CLASSES =
  "rounded-tile font-semibold transition-colors " +
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-700 " +
  "disabled:cursor-not-allowed";

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:
    "bg-brand-700 text-white px-4 py-3 text-body hover:bg-brand-800 active:bg-brand-800 " +
    "disabled:bg-canvas disabled:text-ink-500",
  secondary:
    "bg-surface text-brand-700 border border-brand-700 px-4 py-3 text-body " +
    "hover:bg-brand-50 active:bg-brand-100 disabled:border-line disabled:text-ink-500",
  accent:
    "bg-accent-500 text-white px-4 py-3 text-lead font-bold hover:bg-accent-600 " +
    "active:bg-accent-700 disabled:bg-canvas disabled:text-ink-500",
  link:
    "self-start bg-transparent text-brand-700 underline px-2 py-2 text-body " +
    "hover:text-brand-800 active:text-brand-800 disabled:text-ink-500 disabled:no-underline",
};

export function Button({ variant = "primary", className = "", ...props }: ButtonProps) {
  const classes = `${BASE_CLASSES} ${VARIANT_CLASSES[variant]} ${className}`;
  return <button className={classes} {...props} />;
}
