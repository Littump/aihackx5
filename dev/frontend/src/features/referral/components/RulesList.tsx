import { Card } from "@/shared/ui/Card";

type RulesListProps = {
  rules: string[];
};

export function RulesList({ rules }: RulesListProps) {
  return (
    <Card className="flex flex-col gap-2">
      <h2 className="text-sm font-semibold text-text">Как это работает</h2>
      <ul className="flex flex-col gap-1 text-sm text-text-secondary">
        {rules.map((rule) => (
          <li key={rule} className="flex gap-2">
            <span aria-hidden="true">•</span>
            <span>{rule}</span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
