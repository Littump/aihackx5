/** Переиспользуемые слои фигуры персонажа: шерсть, шапка и предметы обжитости дома. */
export function FurLayer() {
  return (
    <g id="dom-fur">
      <circle cx="12" cy="26" r="5" className="fill-fur-300" />
      <circle cx="52" cy="26" r="5" className="fill-fur-300" />
      <circle cx="9" cy="36" r="5" className="fill-fur-300" />
      <circle cx="55" cy="36" r="5" className="fill-fur-300" />
      <circle cx="15" cy="48" r="5" className="fill-fur-300" />
      <circle cx="49" cy="48" r="5" className="fill-fur-300" />
      <path
        d="M32 10c14 0 22 9 22 22s-9 24-22 24-22-11-22-24 8-22 22-22z"
        className="fill-fur-200"
      />
      <ellipse cx="32" cy="34" rx="16" ry="14" className="fill-fur-100" />
      <ellipse cx="32" cy="46" rx="11" ry="8" className="fill-fur-100" />
      <circle cx="17" cy="38" r="4" className="fill-accent-300" opacity=".7" />
      <circle cx="47" cy="38" r="4" className="fill-accent-300" opacity=".7" />
      <path d="M32 36l4 4h-8z" className="fill-accent-500" />
    </g>
  );
}

export function CapLayer() {
  return (
    <g id="dom-cap">
      <path d="M12 22C18 8 46 8 52 22z" className="fill-brand-600" />
      <rect x="9" y="19" width="46" height="8" rx="4" className="fill-brand-700" />
      <circle cx="32" cy="7" r="5" className="fill-accent-500" />
    </g>
  );
}

export function BlanketLayer() {
  return (
    <g id="dom-blanket">
      <path d="M11 42c8 11 34 11 42 0v11c-8 10-34 10-42 0z" className="fill-brand-500" />
      <path d="M12 48c8 9 32 9 40 0" fill="none" className="stroke-brand-100" strokeWidth="2.5" />
    </g>
  );
}

export function CupLayer() {
  return (
    <g id="dom-cup">
      <rect
        x="44"
        y="50"
        width="13"
        height="11"
        rx="3"
        className="fill-surface stroke-brand-700"
        strokeWidth="2"
      />
      <path
        d="M57 53h3a3 3 0 0 1 0 5h-3"
        fill="none"
        className="stroke-brand-700"
        strokeWidth="2"
      />
    </g>
  );
}

export function ShelfLayer() {
  return (
    <g id="dom-shelf">
      <rect x="2" y="16" width="20" height="3" rx="1.5" className="fill-fur-300" />
      <rect x="4" y="7" width="7" height="9" rx="2" className="fill-accent-300" />
      <rect x="13" y="9" width="7" height="7" rx="2" className="fill-brand-300" />
    </g>
  );
}
