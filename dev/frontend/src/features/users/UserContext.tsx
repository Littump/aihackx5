import { useCallback, useEffect, useMemo, type ReactNode } from "react";
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
  const userId = readUserId(searchParams);

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
    const firstUserId = users.data?.items[0]?.id;
    if (userId !== null || firstUserId === undefined) return;
    setSearchParams(
      (previous) => {
        const next = new URLSearchParams(previous);
        next.set(USER_PARAM, String(firstUserId));
        return next;
      },
      { replace: true },
    );
  }, [userId, users.data, setSearchParams]);

  const value = useMemo(() => ({ userId, setUserId }), [userId, setUserId]);

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}
