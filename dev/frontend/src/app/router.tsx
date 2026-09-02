import { createBrowserRouter } from "react-router";
import { PhoneShell } from "@/shared/ui/PhoneShell";
import { HomeScreen } from "@/features/home/HomeScreen";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <PhoneShell />,
    children: [{ index: true, element: <HomeScreen /> }],
  },
]);
