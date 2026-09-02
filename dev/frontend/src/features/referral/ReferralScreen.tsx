import { Card } from "@/shared/ui/Card";

export function ReferralScreen() {
  return (
    <section className="flex flex-1 flex-col gap-4 p-5">
      <h1 className="text-2xl font-semibold text-text">Позови соседа</h1>
      <Card>
        <p className="text-text-secondary">Экран появится в задаче FE-005.</p>
      </Card>
    </section>
  );
}
