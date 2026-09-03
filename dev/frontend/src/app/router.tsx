import { createBrowserRouter, type RouteObject } from "react-router";
import { RootLayout } from "./RootLayout";
import { ConsumerLayout } from "./ConsumerLayout";
import { PmLayout } from "./PmLayout";
import { HomeScreen } from "@/features/home/HomeScreen";
import { ChallengeScreen } from "@/features/challenge/ChallengeScreen";
import { LeagueScreen } from "@/features/league/LeagueScreen";
import { ReferralScreen } from "@/features/referral/ReferralScreen";
import { PmScreen } from "@/features/pm/PmScreen";

export const routes: RouteObject[] = [
  {
    path: "/",
    element: <RootLayout />,
    children: [
      {
        element: <ConsumerLayout />,
        children: [
          { index: true, element: <HomeScreen /> },
          { path: "challenge", element: <ChallengeScreen /> },
          { path: "league", element: <LeagueScreen /> },
          { path: "referral", element: <ReferralScreen /> },
        ],
      },
    ],
  },
  {
    path: "/pm",
    element: <PmLayout />,
    children: [{ index: true, element: <PmScreen /> }],
  },
];

export const router = createBrowserRouter(routes);
