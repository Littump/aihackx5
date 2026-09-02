import { useHealth } from "./hooks";

export function HomeScreen() {
  const health = useHealth();
  return (
    <section className="flex flex-1 flex-col gap-4 p-5">
      <h1 className="text-2xl font-semibold">Домовой</h1>
      <p className="text-gray-600">Экран Home появится в задаче FE-002.</p>
      <div className="rounded-xl bg-gray-50 p-4 text-sm" data-testid="health">
        {health.isPending && "Проверяем связь…"}
        {health.isError && `Backend недоступен: ${health.error.message}`}
        {health.data && `Backend: ${health.data.status}, база: ${health.data.database}`}
      </div>
    </section>
  );
}
