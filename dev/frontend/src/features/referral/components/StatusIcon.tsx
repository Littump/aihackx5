import type { ReferralStatusIconShape } from "../format";

type StatusIconProps = {
  shapes: ReferralStatusIconShape[];
  className?: string;
};

export function StatusIcon({ shapes, className = "h-6 w-6" }: StatusIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      className={className}
      aria-hidden="true"
    >
      {shapes.map((shape, index) =>
        shape.tag === "path" ? (
          <path key={index} d={shape.d} />
        ) : (
          <circle key={index} cx={shape.cx} cy={shape.cy} r={shape.r} />
        ),
      )}
    </svg>
  );
}
