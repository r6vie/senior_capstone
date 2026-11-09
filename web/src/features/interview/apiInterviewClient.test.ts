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

  it("sends words still in the field with finishing", async () => {
    const post = vi.spyOn(api, "POST").mockResolvedValue(ok(interview({})));
    await apiInterviewClient.finish("me", "My last thought");
    expect(post).toHaveBeenCalledWith("/interview/finish", { body: { answer: "My last thought" } });
  });

  it("uses the back cover shown, or keeps the old one, and never sends its text", async () => {
    const post = vi
      .spyOn(api, "POST")
      .mockResolvedValue(ok({ title: "T", author_name: "A", blurb: null, status: "on_shelf", chapters: [] }));
    await apiInterviewClient.applyChanges(["1"], "The new back cover.");
    expect(post).toHaveBeenLastCalledWith("/interview/revision", { body: { approved: ["1"], blurb: "use" } });
    await apiInterviewClient.applyChanges(["1"], null);
    expect(post).toHaveBeenLastCalledWith("/interview/revision", {
      body: { approved: ["1"], blurb: "keep" },
    });
  });

  it("proposes a removal once, then confirms it like any change", async () => {
    const removal = {
      id: "x",
      kind: "remove",
      chapter_id: "c9",
      title: "T",
      summary: "",
      note: "",
      current: null,
    };
    vi.spyOn(api, "GET").mockResolvedValue(ok(interview({ question: null, stage: "done" })));
    const post = vi
      .spyOn(api, "POST")
      .mockResolvedValueOnce(ok({ ...interview({ question: null }), stage: "revising", changes: [removal] }))
      .mockResolvedValueOnce(ok({ blurb: "Shorter." }))
      .mockResolvedValueOnce(
        ok({ title: "T", author_name: "A", blurb: null, status: "on_shelf", chapters: [] }),
      );
    await expect(apiInterviewClient.blurbWithout("c9")).resolves.toBe("Shorter.");
    expect(post).toHaveBeenCalledWith("/interview/removal", { body: { chapter_id: "c9" } });
    await apiInterviewClient.removeFromShelf("c9", "Shorter.");
    expect(post).toHaveBeenLastCalledWith("/interview/revision", { body: { approved: ["x"], blurb: "use" } });
    expect(post.mock.calls.filter((call) => String(call[0]) === "/interview/removal")).toHaveLength(1);
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

  it("maps a round of new questions to the adding round", async () => {
    vi.spyOn(api, "GET").mockResolvedValue(ok({ ...interview({}), stage: "adding" }));
    await expect(apiInterviewClient.current()).resolves.toMatchObject({ stage: "asking", round: "adding" });
  });

  it("maps proposed changes, and marks what's new", async () => {
    const change = { quotes: [], title: "T", summary: "S", note: "N" };
    vi.spyOn(api, "GET").mockResolvedValue(
      ok({
        ...interview({ question: null, blurb: "Old." }),
        revision_status: "ready",
        stage: "revising",
        changes: [
          { ...change, id: "1", kind: "new", chapter_id: null, current: null },
          { ...change, id: "2", kind: "improve", chapter_id: "c", current: { title: "T0", summary: "S0" } },
        ],
      }),
    );
    await expect(apiInterviewClient.current()).resolves.toMatchObject({
      stage: "proposing",
      blurb: "Old.",
      changes: [
        { id: "1", kind: "new", now: null },
        { id: "2", kind: "improve", now: { title: "T0", summary: "S0" } },
      ],
    });
  });

  it("follows the API's word on whether changes are being written or failed", async () => {
    const revising = (revision_status: string) =>
      ok({ ...interview({ question: null }), stage: "revising", changes: null, revision_status });
    vi.spyOn(api, "GET").mockResolvedValueOnce(revising("writing")).mockResolvedValueOnce(revising("failed"));
    await expect(apiInterviewClient.current()).resolves.toMatchObject({ stage: "writing" });
    await expect(apiInterviewClient.current()).resolves.toMatchObject({ stage: "writeFailed" });
  });

  it("says a round that earned nothing is nothing", async () => {
    vi.spyOn(api, "GET").mockResolvedValue(
      ok({ ...interview({ question: null, stage: "done" }), nothing_new: true }),
    );
    await expect(apiInterviewClient.current()).resolves.toMatchObject({ stage: "nothing" });
  });

  it("reads My book's stage without asking the Librarian for anything", async () => {
    const post = vi.spyOn(api, "POST");
    vi.spyOn(api, "GET").mockResolvedValue(ok(interview({ question: null })));
    await expect(apiInterviewClient.stage()).resolves.toBe("interviewing");
    expect(post).not.toHaveBeenCalled();
  });

  it("counts a round with no answers as closed on My book", async () => {
    vi.spyOn(api, "GET").mockResolvedValue(ok({ ...interview({ can_finish: false }), stage: "adding" }));
    await expect(apiInterviewClient.stage()).resolves.toBe("shelf");
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
