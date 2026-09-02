import { Card } from "@/shared/ui/Card";

export function PmScreen() {
  return (
    <section className="flex flex-1 flex-col gap-4 p-5">
      <h1 className="text-2xl font-semibold text-text">PM view</h1>
      <Card>
        <p className="text-text-secondary">Экран появится в задаче FE-006.</p>
      </Card>
    </section>
  );
}
