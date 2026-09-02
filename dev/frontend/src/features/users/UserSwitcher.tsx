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
    <div className="flex items-center gap-2 border-b border-border bg-brand-100 px-4 py-2">
      <label htmlFor="user-switcher" className="text-xs text-text-secondary">
        Пользователь
      </label>
      <select
        id="user-switcher"
        aria-label="Переключить пользователя"
        className="flex-1 rounded-lg border border-border bg-surface px-2 py-1 text-sm text-text"
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
