import { act, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "./AuthProvider";

const api = vi.hoisted(() => ({ GET: vi.fn(), POST: vi.fn() }));
const session = vi.hoisted(() => ({ get: vi.fn(() => null), set: vi.fn(), clear: vi.fn() }));

vi.mock("../../api/client", () => ({ api, session, SESSION_ENDED: "trove:session-ended" }));

function Who() {
  const { user, sessionEnded } = useAuth();
  return <p>{user ? "signed in" : sessionEnded ? "session ended" : "signed out"}</p>;
}

function SignOut() {
  const { signOut } = useAuth();
  return (
    <button type="button" onClick={() => signOut()}>
      Sign out
    </button>
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    localStorage.clear();
    api.POST.mockResolvedValue({ data: {}, response: { status: 204 } });
  });

  it("clears interview drafts on sign-out, so the next person on this computer can't read them", async () => {
    localStorage.setItem("trove_interview_draft:u1:What do you know?", "half an answer");
    localStorage.setItem("something_else", "kept");
    render(
      <AuthProvider>
        <SignOut />
      </AuthProvider>,
    );

    await act(async () => screen.getByRole("button", { name: "Sign out" }).click());

    expect(localStorage.getItem("trove_interview_draft:u1:What do you know?")).toBeNull();
    expect(localStorage.getItem("something_else")).toBe("kept");
    expect(session.clear).toHaveBeenCalled();
  });

  it("signs out where the member is when the session ends, keeping their unsent drafts", async () => {
    session.get.mockReturnValue("token" as never);
    api.GET.mockResolvedValue({ data: { id: "u1" }, response: { status: 200 } });
    localStorage.setItem("trove_interview_draft:u1:What do you know?", "half an answer");
    render(
      <AuthProvider>
        <Who />
      </AuthProvider>,
    );
    expect(await screen.findByText("signed in")).toBeTruthy();

    await act(async () => window.dispatchEvent(new Event("trove:session-ended")));

    expect(screen.getByText("session ended")).toBeTruthy();
    expect(localStorage.getItem("trove_interview_draft:u1:What do you know?")).toBe("half an answer");
    session.get.mockReturnValue(null);
  });
});
