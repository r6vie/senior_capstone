import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// The client keeps the fetch and Request it finds when it is made, so both are set first: Request resolves its
// relative /api URLs as the browser would.
const NativeRequest = globalThis.Request;
class PageRequest extends NativeRequest {
  constructor(input: RequestInfo | URL, init?: RequestInit) {
    super(typeof input === "string" ? new URL(input, "http://localhost") : input, init);
  }
}
vi.stubGlobal("Request", PageRequest);
// Every call is answered as a server that no longer knows the session.
vi.stubGlobal(
  "fetch",
  vi.fn(async () => new Response(null, { status: 401 })),
);
const { api, SESSION_ENDED, session } = await import("./client");

describe("api", () => {
  const ended = vi.fn<(event: Event) => void>();
  beforeEach(() => {
    ended.mockClear();
    window.addEventListener(SESSION_ENDED, ended);
  });
  afterEach(() => {
    window.removeEventListener(SESSION_ENDED, ended);
    session.clear();
  });

  it("ends the session when a signed-in call finds it gone", async () => {
    session.set("old-token");
    await api.GET("/books/me");
    expect(ended).toHaveBeenCalledTimes(1);
    expect(session.get()).toBeNull();
  });

  it("leaves a wrong password, and calls made while signed out, alone", async () => {
    session.set("old-token");
    await api.POST("/auth/login", { body: { email: "sam@case.edu", password: "wrong password here" } });
    expect(ended).not.toHaveBeenCalled();
    expect(session.get()).toBe("old-token");

    session.clear();
    await api.GET("/books/me");
    expect(ended).not.toHaveBeenCalled();
  });
});
