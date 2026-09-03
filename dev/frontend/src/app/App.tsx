import { RouterProvider } from "react-router";
import { DomovoyDefs } from "@/features/domovoy/DomovoyDefs";
import { Providers } from "./providers";
import { router } from "./router";

export function App() {
  return (
    <Providers>
      <DomovoyDefs />
      <RouterProvider router={router} />
    </Providers>
  );
}
