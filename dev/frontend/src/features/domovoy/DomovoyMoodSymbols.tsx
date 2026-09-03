/** Пять символов персонажа, каждый со своей формой глаз/рта, а не только цветом. */
export function CheerfulSymbol() {
  return (
    <symbol id="dom-cheerful" viewBox="0 0 64 64">
      <use href="#dom-fur" />
      <use href="#dom-cap" />
      <circle cx="24" cy="32" r="4" className="fill-ink-900" />
      <circle cx="40" cy="32" r="4" className="fill-ink-900" />
      <path d="M24 44a8 8 0 0 0 16 0z" className="fill-ink-900" />
      <path
        d="M58 12v7M54.5 15.5h7"
        className="stroke-accent-500"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <path
        d="M6 16v6M3 19h6"
        className="stroke-accent-500"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </symbol>
  );
}

export function CozySymbol() {
  return (
    <symbol id="dom-cozy" viewBox="0 0 64 64">
      <use href="#dom-fur" />
      <use href="#dom-cap" />
      <path
        d="M19 33a5 5 0 0 1 10 0M35 33a5 5 0 0 1 10 0"
        fill="none"
        className="stroke-ink-900"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <path
        d="M27 45a5 5 0 0 0 10 0"
        fill="none"
        className="stroke-ink-900"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <use href="#dom-blanket" />
    </symbol>
  );
}

export function HealthySymbol() {
  return (
    <symbol id="dom-healthy" viewBox="0 0 64 64">
      <use href="#dom-fur" />
      <use href="#dom-cap" />
      <circle cx="24" cy="33" r="4.5" className="fill-ink-900" />
      <circle cx="40" cy="33" r="4.5" className="fill-ink-900" />
      <path
        d="M18 26q6-5 12-1M34 25q6-4 12 1"
        fill="none"
        className="stroke-ink-900"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <path d="M22 43q10 8 20 0z" className="fill-ink-900" />
      <path d="M46 42c0-14 8-22 18-24 2 14-4 24-18 24z" className="fill-brand-500" />
      <path
        d="M50 40c4-8 8-13 13-16"
        fill="none"
        className="stroke-brand-100"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
    </symbol>
  );
}

export function BoredSymbol() {
  return (
    <symbol id="dom-bored" viewBox="0 0 64 64">
      <use href="#dom-fur" />
      <g transform="rotate(-14 32 24)">
        <use href="#dom-cap" />
      </g>
      <path
        d="M18 31h12M34 31h12"
        className="stroke-ink-900"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <circle cx="26" cy="35" r="3" className="fill-ink-900" />
      <circle cx="42" cy="35" r="3" className="fill-ink-900" />
      <path d="M25 46h14" className="stroke-ink-900" strokeWidth="3" strokeLinecap="round" />
    </symbol>
  );
}

export function SleepySymbol() {
  return (
    <symbol id="dom-sleepy" viewBox="0 0 64 64">
      <use href="#dom-fur" />
      <path d="M12 24C16 8 44 6 50 20l8 14a6 6 0 0 1-9 3l-6-9z" className="fill-brand-600" />
      <rect x="9" y="21" width="44" height="8" rx="4" className="fill-brand-700" />
      <circle cx="54" cy="38" r="5" className="fill-accent-500" />
      <path
        d="M19 34q5 5 10 0M35 34q5 5 10 0"
        fill="none"
        className="stroke-ink-900"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <ellipse cx="32" cy="46" rx="4" ry="3" className="fill-ink-900" />
      <text
        x="4"
        y="16"
        fontSize="14"
        fontWeight="700"
        fontFamily="ui-sans-serif, system-ui"
        className="fill-brand-700"
      >
        z
      </text>
      <text
        x="14"
        y="8"
        fontSize="9"
        fontWeight="700"
        fontFamily="ui-sans-serif, system-ui"
        className="fill-brand-500"
      >
        z
      </text>
    </symbol>
  );
}
