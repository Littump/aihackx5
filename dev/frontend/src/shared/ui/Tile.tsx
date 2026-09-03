import type { ReactNode } from "react";
import { Link } from "react-router";

type TileProps = {
  icon?: ReactNode;
  title: string;
  subtitle?: string;
  to?: string;
  href?: string;
  className?: string;
};

const TILE_CLASSES =
  "flex flex-col gap-2 rounded-tile bg-surface p-4 shadow-card text-ink-900 no-underline " +
  "hover:bg-brand-50 active:bg-brand-100 focus-visible:outline-2 focus-visible:outline-offset-2 " +
  "focus-visible:outline-brand-700";

export function Tile({ icon, title, subtitle, to, href, className = "" }: TileProps) {
  const classes = `${TILE_CLASSES} ${className}`;
  const content = (
    <>
      {icon && (
        <span className="h-6 w-6 text-brand-700" aria-hidden="true">
          {icon}
        </span>
      )}
      <span className="text-body font-semibold leading-tight">{title}</span>
      {subtitle && <span className="text-caption text-ink-500">{subtitle}</span>}
    </>
  );
  if (to) {
    return (
      <Link to={to} className={classes}>
        {content}
      </Link>
    );
  }
  if (href) {
    return (
      <a href={href} className={classes}>
        {content}
      </a>
    );
  }
  return <div className={classes}>{content}</div>;
}
