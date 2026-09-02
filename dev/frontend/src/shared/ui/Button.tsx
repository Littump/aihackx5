import type { ButtonHTMLAttributes } from "react";

type ButtonVariant = "primary" | "secondary";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
};

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary: "bg-brand-600 text-white hover:bg-brand-900",
  secondary: "border border-brand-600 text-brand-600 hover:bg-brand-100",
};

export function Button({ variant = "primary", className = "", ...props }: ButtonProps) {
  const classes =
    `rounded-xl px-4 py-2 text-sm font-medium transition-colors ` +
    `disabled:cursor-not-allowed disabled:opacity-50 ${VARIANT_CLASSES[variant]} ${className}`;
  return <button className={classes} {...props} />;
}
