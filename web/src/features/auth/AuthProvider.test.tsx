import { act, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "./AuthProvider";

const api = vi.hoisted(() => ({ GET: vi.fn(), POST: vi.fn() }));
const session = vi.hoisted(() => ({ get: vi.fn(() => null), set: vi.fn(), clear: vi.fn() }));

vi.mock("../../api/client", () => ({ api, session }));

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
});
