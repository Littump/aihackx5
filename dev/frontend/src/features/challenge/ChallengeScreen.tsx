import { Card } from "@/shared/ui/Card";

export function ChallengeScreen() {
  return (
    <section className="flex flex-1 flex-col gap-4 p-5">
      <h1 className="text-2xl font-semibold text-text">Челлендж</h1>
      <Card>
        <p className="text-text-secondary">Экран появится в задаче FE-003.</p>
      </Card>
    </section>
  );
}
