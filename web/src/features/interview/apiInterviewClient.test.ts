import { api } from "../../api/client";
import type { components } from "../../api/schema";
import { apiInterviewClient } from "./apiInterviewClient";

type InterviewResponse = components["schemas"]["InterviewResponse"];

function interview(overrides: Partial<InterviewResponse>): InterviewResponse {
  return {
    stage: "interviewing",
    question: { text: "What do people come to you for?", phase: "sweep", playback: null },
    topic: null,
    has_answers: false,
    can_finish: false,
    ready_for_reveal: false,
    titles: null,
    blurb: null,
    ...overrides,
  };
}

function ok<T>(data: T) {
  return { data, error: undefined, response: new Response(null, { status: 200 }) } as never;
}

describe("apiInterviewClient", () => {
  afterEach(() => vi.restoreAllMocks());

  it("treats a missing interview as not started", async () => {
    vi.spyOn(api, "GET").mockResolvedValue({
      data: undefined,
      error: { detail: "Not started" },
      response: new Response(null, { status: 404 }),
    } as never);
    expect(await apiInterviewClient.current()).toBeNull();
  });

  it("shows the Shape step as the playback followed by its question", async () => {
    vi.spyOn(api, "POST").mockResolvedValue(
      ok(
        interview({
          question: { text: "Is this you?", phase: "shape", playback: "You left grad school twice." },
        }),
      ),
    );
    expect(await apiInterviewClient.answer("me", "An answer")).toEqual({
      id: "me",
      stage: "shaping",
      phase: "shape",
      playback: "You left grad school twice. Is this you?",
    });
  });

  it("goes straight to the titles when the Librarian has enough", async () => {
    const post = vi
      .spyOn(api, "POST")
      .mockResolvedValueOnce(ok(interview({ question: null, ready_for_reveal: true })))
      .mockResolvedValueOnce(
        ok(interview({ stage: "choosing", question: null, titles: [{ title: "A", why: "B" }] })),
      );
    const state = await apiInterviewClient.confirmShape("me");
    expect(post).toHaveBeenLastCalledWith("/interview/finish");
    expect(state).toEqual({ id: "me", stage: "choosing", titles: [{ id: "0", title: "A", why: "B" }] });
  });

  it("asks for the question again once when it couldn't be written", async () => {
    const post = vi
      .spyOn(api, "POST")
      .mockResolvedValueOnce(ok(interview({ question: null })))
      .mockResolvedValueOnce(ok(interview({})));
    const state = await apiInterviewClient.answer("me", "An answer");
    expect(post).toHaveBeenLastCalledWith("/interview/question");
    expect(state).toMatchObject({ stage: "asking", question: "What do people come to you for?" });
  });

  it("marks the Librarian's failures as safe to try again", async () => {
    vi.spyOn(api, "POST").mockResolvedValue({
      data: undefined,
      error: { detail: "The Librarian couldn't answer just now. Please try again." },
      response: new Response(null, { status: 502 }),
    } as never);
    await expect(apiInterviewClient.answer("me", "An answer")).rejects.toMatchObject({ retryable: true });
  });

  it("shows the API's sentence when a call fails", async () => {
    vi.spyOn(api, "POST").mockResolvedValue({
      data: undefined,
      error: { detail: "A book needs at least 3 chapters." },
      response: new Response(null, { status: 409 }),
    } as never);
    await expect(apiInterviewClient.putOnShelf("me")).rejects.toThrow("A book needs at least 3 chapters.");
  });
});
