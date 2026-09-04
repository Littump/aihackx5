import { http, HttpResponse, type PathParams } from "msw";
import {
  USERS,
  buildReceiptProcessingResult,
  getAchievements,
  getChallengeDetail,
  getChallengeList,
  getEvalRun,
  getFraudChecks,
  getHome,
  getLeague,
  getPmUser,
  getReceipts,
  getReferral,
  getSimulateDraft,
  getSimulationRun,
} from "./fixtures";

export const API = "http://localhost:8000/api/v1";

function userIdParam(params: PathParams): number {
  const raw = params.user_id;
  return Number(Array.isArray(raw) ? raw[0] : raw);
}

export const handlers = [
  http.get(`${API}/health`, () => HttpResponse.json({ status: "ok", database: "ok" })),

  http.get(`${API}/users`, () => HttpResponse.json({ items: USERS })),

  http.get(`${API}/users/:user_id/home`, ({ params }) =>
    HttpResponse.json(getHome(userIdParam(params))),
  ),

  http.get(`${API}/users/:user_id/savings`, ({ params }) =>
    HttpResponse.json(getHome(userIdParam(params)).savings),
  ),

  http.get(`${API}/users/:user_id/challenges`, ({ params }) =>
    HttpResponse.json(getChallengeList(userIdParam(params))),
  ),

  http.post(`${API}/users/:user_id/challenges/refresh`, ({ params }) =>
    HttpResponse.json(getChallengeList(userIdParam(params))),
  ),

  http.get(`${API}/users/:user_id/challenges/:challenge_id`, ({ params }) =>
    HttpResponse.json(getChallengeDetail(userIdParam(params), Number(params.challenge_id))),
  ),

  http.post(`${API}/receipts`, async ({ request }) => {
    const body = (await request.json()) as { user_id: number };
    return HttpResponse.json(buildReceiptProcessingResult(body.user_id), { status: 201 });
  }),

  http.get(`${API}/users/:user_id/receipts/simulate/draft`, ({ params }) =>
    HttpResponse.json(getSimulateDraft(userIdParam(params))),
  ),

  http.post(`${API}/users/:user_id/receipts/simulate`, ({ params }) =>
    HttpResponse.json(buildReceiptProcessingResult(userIdParam(params)), { status: 201 }),
  ),

  http.get(`${API}/users/:user_id/receipts`, () => HttpResponse.json({ items: getReceipts() })),

  http.get(`${API}/users/:user_id/league`, ({ params }) =>
    HttpResponse.json(getLeague(userIdParam(params))),
  ),

  http.get(`${API}/users/:user_id/referral`, ({ params }) =>
    HttpResponse.json(getReferral(userIdParam(params))),
  ),

  http.post(`${API}/referrals/redeem`, () =>
    HttpResponse.json(
      { referee_user_id: 4, referrer_user_id: 1, referee_kind: "new", status: "pending" },
      { status: 201 },
    ),
  ),

  http.get(`${API}/users/:user_id/achievements`, () =>
    HttpResponse.json({ items: getAchievements() }),
  ),

  http.get(`${API}/pm/users/:user_id`, ({ params }) =>
    HttpResponse.json(getPmUser(userIdParam(params))),
  ),

  http.get(`${API}/pm/fraud`, ({ request }) => {
    const decision = new URL(request.url).searchParams.get("decision");
    const items = getFraudChecks().filter((check) => !decision || check.decision === decision);
    return HttpResponse.json({ items });
  }),

  http.get(`${API}/pm/simulation/latest`, () => HttpResponse.json(getSimulationRun())),

  http.get(`${API}/pm/eval/latest`, () => HttpResponse.json(getEvalRun())),
];
