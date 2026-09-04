import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { useSearchParams } from "react-router";
import { UserContext } from "./context";
import { useUsers } from "./hooks";

const USER_PARAM = "user";

function readUserId(searchParams: URLSearchParams): number | null {
  const raw = searchParams.get(USER_PARAM);
  const parsed = raw === null ? NaN : Number(raw);
  return Number.isFinite(parsed) ? parsed : null;
}

export function UserProvider({ children }: { children: ReactNode }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const users = useUsers();
  const urlUserId = readUserId(searchParams);
  const [lastUserId, setLastUserId] = useState<number | null>(urlUserId);
  const userId = urlUserId ?? lastUserId;

  const setUserId = useCallback(
    (id: number) => {
      setSearchParams(
        (previous) => {
          const next = new URLSearchParams(previous);
          next.set(USER_PARAM, String(id));
          return next;
        },
        { replace: false },
      );
    },
    [setSearchParams],
  );

  useEffect(() => {
    if (urlUserId !== null && urlUserId !== lastUserId) setLastUserId(urlUserId);
  }, [urlUserId, lastUserId]);

  useEffect(() => {
    if (urlUserId !== null) return;
    const restoredId = lastUserId ?? users.data?.items[0]?.id;
    if (restoredId === undefined || restoredId === null) return;
    setSearchParams(
      (previous) => {
        const next = new URLSearchParams(previous);
        next.set(USER_PARAM, String(restoredId));
        return next;
      },
      { replace: true },
    );
  }, [urlUserId, lastUserId, users.data, setSearchParams]);

  const value = useMemo(() => ({ userId, setUserId }), [userId, setUserId]);

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}
