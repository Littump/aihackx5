import type { ChangeEvent } from "react";
import { useUserContext, useUsers } from "./hooks";

export function UserSwitcher() {
  const { userId, setUserId } = useUserContext();
  const users = useUsers();

  function handleChange(event: ChangeEvent<HTMLSelectElement>) {
    setUserId(Number(event.target.value));
  }

  const options = users.data?.items ?? [];

  return (
    <div className="flex shrink-0 items-center gap-3 bg-ink-900 px-4 py-2 text-white">
      <span className="text-caption font-mono uppercase tracking-wider text-brand-300">Демо</span>
      <select
        id="user-switcher"
        aria-label="Переключить пользователя"
        className="min-w-0 flex-1 rounded-tile border border-white/20 bg-ink-700 px-3 py-2 text-caption text-white"
        value={userId ?? ""}
        onChange={handleChange}
        disabled={options.length === 0}
      >
        {options.length === 0 && <option value="">Загрузка…</option>}
        {options.map((user) => (
          <option key={user.id} value={user.id}>
            {user.pseudonym} · ур. {user.level}
          </option>
        ))}
      </select>
    </div>
  );
}
