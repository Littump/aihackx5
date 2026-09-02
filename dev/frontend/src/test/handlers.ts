import { http, HttpResponse } from "msw";

export const API = "http://localhost:8000/api/v1";

export const handlers = [
  http.get(`${API}/health`, () => HttpResponse.json({ status: "ok", database: "ok" })),
];
