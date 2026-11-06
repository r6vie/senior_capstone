import createClient from "openapi-fetch";
import type { paths } from "./schema";

// schema.ts is generated from the backend (scripts/generate_api_client.py). Never edit it by hand.
// Every call is typed from the backend's models: if the API changes, TypeScript shows what broke.

const SESSION_KEY = "trove_session";

export const session = {
  get: () => sessionStorage.getItem(SESSION_KEY),
  set: (token: string) => sessionStorage.setItem(SESSION_KEY, token),
  clear: () => sessionStorage.removeItem(SESSION_KEY),
};

export const api = createClient<paths>({ baseUrl: "/api" });

api.use({
  onRequest({ request }) {
    const token = session.get();
    if (token) request.headers.set("Authorization", `Bearer ${token}`);
    return request;
  },
});
