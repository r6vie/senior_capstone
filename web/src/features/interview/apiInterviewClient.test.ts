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
    needs_more: false,
    at_limit: false,
    titles: null,
    blurb: null,
    revision_status: null,
    changes: null,
    proposed_blurb: null,
    nothing_new: false,
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

  it("moves past a question without sending an answer", async () => {
    const post = vi.spyOn(api, "POST").mockResolvedValue(ok(interview({})));
    const state = await apiInterviewClient.skip("me");
    expect(post).toHaveBeenCalledWith("/interview/skip");
    expect(state).toMatchObject({ stage: "asking" });
  });

  it("saves words still in the field before finishing", async () => {
    const post = vi.spyOn(api, "POST").mockResolvedValue(ok(interview({})));
    await apiInterviewClient.finish("me", "My last thought");
    expect(post).toHaveBeenCalledWith("/interview/answers", { body: { answer: "My last thought" } });
    expect(post).toHaveBeenLastCalledWith("/interview/finish");
  });

  it("marks the Librarian's failures as safe to try again", async () => {
    vi.spyOn(api, "POST").mockResolvedValue({
      data: undefined,
      error: { detail: "The Librarian couldn't answer just now. Please try again." },
      response: new Response(null, { status: 502 }),
    } as never);
    await expect(apiInterviewClient.answer("me", "An answer")).rejects.toMatchObject({ retryable: true });
  });

  it("never shows a member the API's words for a database or a field", async () => {
    const fails = (status: number, detail: unknown) =>
      vi.spyOn(api, "POST").mockResolvedValueOnce({
        data: undefined,
        error: { detail },
        response: new Response(null, { status }),
      } as never);
    fails(503, "The database is unavailable.");
    await expect(apiInterviewClient.answer("me", "An answer")).rejects.toThrow(
      "Something's wrong on our side. Nothing you said is lost.",
    );
    fails(422, [{ loc: ["body", "answer"], msg: "String should have at most 5000 characters" }]);
    await expect(apiInterviewClient.answer("me", "An answer")).rejects.toThrow(
      "That didn't go through. Check it and try again.",
    );
  });

  it("carries a chapter's quotes to the member's own review", async () => {
    vi.spyOn(api, "POST").mockResolvedValue(
      ok({
        title: "T",
        author_name: "A",
        blurb: null,
        status: "draft",
        chapters: [{ id: "1", title: "C", summary: "S", quotes: ["My words."] }],
      }),
    );
    const state = await apiInterviewClient.rewriteChapter("me", "1");
    expect(state).toMatchObject({ stage: "reviewing", book: { chapters: [{ quotes: ["My words."] }] } });
  });

  it("when a title was already chosen, goes on to where the interview really is", async () => {
    vi.spyOn(api, "POST").mockResolvedValue({
      data: undefined,
      error: { detail: "You already have a book." },
      response: new Response(null, { status: 409 }),
    } as never);
    vi.spyOn(api, "GET")
      .mockResolvedValueOnce(ok(interview({ stage: "reviewing", question: null })))
      .mockResolvedValueOnce(
        ok({ title: "T", author_name: "A", blurb: null, status: "draft", chapters: [] }),
      );
    await expect(apiInterviewClient.chooseTitle("me", "1")).resolves.toMatchObject({ stage: "reviewing" });
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
