import { useQuery } from "@tanstack/react-query";
import { useContext } from "react";
import { getUsers } from "./api";
import { UserContext, type UserContextValue } from "./context";

export function useUsers() {
  return useQuery({ queryKey: ["users"], queryFn: getUsers, staleTime: 60_000 });
}

export function useUserContext(): UserContextValue {
  const context = useContext(UserContext);
  if (context === null) throw new Error("useUserContext вызван вне UserProvider");
  return context;
}
