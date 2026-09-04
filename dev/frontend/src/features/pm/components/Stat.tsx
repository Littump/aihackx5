type StatProps = {
  label: string;
  value: string;
  valueClassName?: string;
};

export function Stat({ label, value, valueClassName = "" }: StatProps) {
  return (
    <div className="flex flex-col">
      <dt className="text-caption text-ink-500">{label}</dt>
      <dd className={`m-0 text-body font-semibold text-ink-900 ${valueClassName}`}>{value}</dd>
    </div>
  );
}
