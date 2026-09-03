type RulesListProps = {
  rules: string[];
};

export function RulesList({ rules }: RulesListProps) {
  return (
    <section className="flex shrink-0 flex-col gap-3 rounded-card bg-surface p-4 shadow-card">
      <h3 className="text-lead font-bold">Правила</h3>
      <ul className="m-0 flex list-none flex-col gap-2 pl-0">
        {rules.map((rule, index) => (
          <li key={rule} className="flex gap-2 text-body text-ink-700">
            <span className="font-bold text-brand-700">{index + 1}.</span>
            {rule}
          </li>
        ))}
      </ul>
    </section>
  );
}
