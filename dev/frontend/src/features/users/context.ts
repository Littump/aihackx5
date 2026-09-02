import { createContext } from "react";

export type UserContextValue = {
  userId: number | null;
  setUserId: (id: number) => void;
};

export const UserContext = createContext<UserContextValue | null>(null);
