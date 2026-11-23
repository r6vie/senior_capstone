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

/** Sent when the server no longer knows this browser's session (it ran out, was ended elsewhere, or the server
 *  moved database): AuthProvider then signs the member out where they are, keeping their drafts. */
export const SESSION_ENDED = "trove:session-ended";

api.use({
  onRequest({ request }) {
    const token = session.get();
    if (token) request.headers.set("Authorization", `Bearer ${token}`);
    return request;
  },
  onResponse({ request, response }) {
    // Only a call made with a session can find it ended; signing in or out answers 401 for other reasons.
    const path = new URL(request.url, window.location.origin).pathname;
    if (
      response.status === 401 &&
      request.headers.has("Authorization") &&
      !/\/auth\/(login|logout)$/.test(path)
    ) {
      session.clear();
      window.dispatchEvent(new Event(SESSION_ENDED));
    }
    return response;
  },
});
