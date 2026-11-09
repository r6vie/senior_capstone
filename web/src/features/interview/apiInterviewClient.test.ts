import { api } from "../../api/client";
import type { components } from "../../api/schema";
import { apiInterviewClient } from "./apiInterviewClient";
import { LostError } from "./interviewClient";

type InterviewResponse = components["schemas"]["InterviewResponse"];

function interview(overrides: Partial<InterviewResponse>): InterviewResponse {
  return {
    stage: "interviewing",
    question: { question_id: "q0", text: "What do people come to you for?", phase: "sweep", playback: null },
    topic: null,
    has_answers: false,
    can_finish: false,
    ready_for_reveal: false,
    needs_more: false,
    nearly_done: false,
    step_status: null,
    chosen_title: null,
    approved_changes: null,
    selection_blurb_status: null,
    selection_blurb: null,
    at_limit: false,
    titles: null,
    blurb: null,
    revision_status: null,
    changes: null,
    proposed_blurb: null,
    nothing_new: false,
    dropped_for_names: false,
    reading_question_id: null,
    reading_answer: null,
    dropped_words: null,
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
          question: {
            question_id: "q1",
            text: "Is this you?",
            phase: "shape",
            playback: "You left grad school twice.",
          },
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
    expect(post).toHaveBeenLastCalledWith("/interview/finish", {});
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
    expect(post).toHaveBeenCalledWith("/interview/skip", { body: { question_id: expect.any(String) } });
    expect(state).toMatchObject({ stage: "asking" });
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
    const revising = { ...interview({ question: null }), stage: "revising", changes: [removal] };
    vi.spyOn(api, "GET")
      .mockResolvedValueOnce(ok(interview({ question: null, stage: "done" })))
      .mockResolvedValue(ok({ ...revising, selection_blurb_status: "ready", selection_blurb: "Shorter." }));
    vi.spyOn(api, "PUT").mockResolvedValue(ok(revising));
    const post = vi
      .spyOn(api, "POST")
      .mockResolvedValueOnce(ok(revising))
      .mockResolvedValueOnce(
        ok({ title: "T", author_name: "A", blurb: null, status: "on_shelf", chapters: [] }),
      );
    await expect(apiInterviewClient.blurbWithout("c9")).resolves.toBe("Shorter.");
    expect(post).toHaveBeenCalledWith("/interview/removal", { body: { chapter_id: "c9" } });
    await apiInterviewClient.removeFromShelf("c9", "Shorter.");
    expect(post).toHaveBeenLastCalledWith("/interview/revision", { body: { approved: ["x"], blurb: "use" } });
    expect(post.mock.calls.filter((call) => String(call[0]) === "/interview/removal")).toHaveLength(1);
  });

  describe("the back cover for a selection", () => {
    const revising = (selection_blurb_status: string | null, selection_blurb: string | null = null) =>
      ok({ ...interview({ question: null }), stage: "revising", selection_blurb_status, selection_blurb });

    it("saves the choices, asks for it, and waits until it's written", async () => {
      vi.useFakeTimers({ shouldAdvanceTime: true });
      const put = vi.spyOn(api, "PUT").mockResolvedValue(ok(revising(null)));
      const post = vi.spyOn(api, "POST").mockResolvedValue(ok(revising("writing")));
      vi.spyOn(api, "GET")
        .mockResolvedValueOnce(revising(null))
        .mockResolvedValueOnce(revising("writing"))
        .mockResolvedValue(revising("ready", "Written."));
      const blurb = apiInterviewClient.blurbFor(["1"]);
      await vi.advanceTimersByTimeAsync(5000);
      await expect(blurb).resolves.toBe("Written.");
      expect(put).toHaveBeenCalledWith("/interview/revision/choices", { body: { approved: ["1"] } });
      expect(post).toHaveBeenCalledTimes(1);
      vi.useRealTimers();
    });

    it("uses one already written, for a member coming back, without another write", async () => {
      vi.spyOn(api, "PUT").mockResolvedValue(ok(revising(null)));
      const post = vi.spyOn(api, "POST");
      vi.spyOn(api, "GET").mockResolvedValue(revising("ready", "Written."));
      await expect(apiInterviewClient.blurbFor(["1"])).resolves.toBe("Written.");
      expect(post).not.toHaveBeenCalled();
    });

    it("gives up when the write fails, so the member can keep the old one", async () => {
      vi.useFakeTimers({ shouldAdvanceTime: true });
      vi.spyOn(api, "PUT").mockResolvedValue(ok(revising(null)));
      vi.spyOn(api, "POST").mockResolvedValue(ok(revising("writing")));
      vi.spyOn(api, "GET").mockResolvedValueOnce(revising(null)).mockResolvedValue(revising("failed"));
      const blurb = apiInterviewClient.blurbFor(["1"]);
      const failed = expect(blurb).rejects.toThrow("couldn't be written");
      await vi.advanceTimersByTimeAsync(5000);
      await failed;
      vi.useRealTimers();
    });
  });

  it("sends words still in the field with finishing, and the question they answer", async () => {
    const post = vi.spyOn(api, "POST").mockResolvedValue(ok(interview({})));
    await apiInterviewClient.askAgain("me");
    await apiInterviewClient.finish("me", "My last thought");
    expect(post).toHaveBeenLastCalledWith("/interview/finish", {
      body: { answer: "My last thought", question_id: "q0" },
    });
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

  it("choosing a title waits for the book, and a failed step can be tried again with that title", async () => {
    const titles = [
      { title: "A", why: "" },
      { title: "B", why: "" },
    ];
    const finishing = (step_status: string) =>
      ok({ ...interview({ question: null, titles }), stage: "finishing", step_status, chosen_title: "B" });
    const post = vi.spyOn(api, "POST").mockResolvedValue(finishing("writing"));
    await expect(apiInterviewClient.chooseTitle("me", "1")).resolves.toMatchObject({
      stage: "drafting",
      about: "book",
    });
    vi.spyOn(api, "GET").mockResolvedValue(finishing("failed"));
    const now = await apiInterviewClient.current();
    expect(now).toMatchObject({ stage: "drafting", failed: true, retryTitle: "1" });
    await apiInterviewClient.retryDrafting("book", "1");
    expect(post).toHaveBeenLastCalledWith("/interview/title", { body: { title: 1 } });
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

  it("tells the API's 502 from a proxy's, which may never have reached it", async () => {
    vi.spyOn(api, "POST").mockResolvedValue({
      data: undefined,
      error: undefined,
      response: new Response(null, { status: 502 }),
    } as never);
    await expect(apiInterviewClient.answer("me", "An answer")).rejects.toBeInstanceOf(LostError);
  });

  it("passes through a sentence the API wrote for the member, but not a schema error", async () => {
    const post = vi.spyOn(api, "POST");
    post.mockResolvedValueOnce({
      data: undefined,
      error: { detail: "We couldn't read any text in that PDF. You can start without it." },
      response: new Response(null, { status: 422 }),
    } as never);
    await expect(apiInterviewClient.start(null)).rejects.toThrow("We couldn't read any text in that PDF");
  });

  it("reads whether a refused answer is the one already saved", async () => {
    vi.spyOn(api, "POST").mockResolvedValue({
      data: undefined,
      error: { detail: "Stale.", already_saved: true },
      response: new Response(null, { status: 409 }),
    } as never);
    await expect(apiInterviewClient.answer("me", "An answer")).rejects.toMatchObject({
      conflict: true,
      alreadySaved: true,
    });
  });

  it("treats undoing an already undone book as success", async () => {
    vi.spyOn(api, "POST").mockResolvedValue({
      data: undefined,
      error: { detail: "Nothing to undo." },
      response: new Response(null, { status: 409 }),
    } as never);
    vi.spyOn(api, "GET").mockResolvedValue(
      ok({ title: "T", author_name: "A", blurb: null, status: "on_shelf", chapters: [], can_undo: false }),
    );
    await expect(apiInterviewClient.undoChanges()).resolves.toBeUndefined();
  });

  it("finds a removal left open only when it's the one open change", async () => {
    const remove = {
      id: "x",
      kind: "remove",
      chapter_id: "c",
      title: "T",
      summary: "",
      note: "",
      current: null,
    };
    vi.spyOn(api, "GET")
      .mockResolvedValueOnce(ok({ ...interview({ question: null }), stage: "revising", changes: [remove] }))
      .mockResolvedValueOnce(
        ok({
          ...interview({ question: null }),
          stage: "revising",
          changes: [remove, { ...remove, id: "y" }],
        }),
      );
    await expect(apiInterviewClient.openRemoval()).resolves.toEqual({ chapterId: "c", title: "T" });
    await expect(apiInterviewClient.openRemoval()).resolves.toBeNull();
  });

  it("marks a 409 as out of date", async () => {
    vi.spyOn(api, "POST").mockResolvedValue({
      data: undefined,
      error: { detail: "There's no question waiting." },
      response: new Response(null, { status: 409 }),
    } as never);
    await expect(apiInterviewClient.answer("me", "An answer")).rejects.toMatchObject({ conflict: true });
  });

  it("sends the question's id back once the API gives one", async () => {
    const post = vi
      .spyOn(api, "POST")
      .mockResolvedValue(
        ok(interview({ question: { question_id: "q1", text: "Q", phase: "sweep", playback: null } })),
      );
    await apiInterviewClient.askAgain("me");
    await apiInterviewClient.answer("me", "An answer");
    expect(post).toHaveBeenLastCalledWith("/interview/answers", {
      body: { answer: "An answer", question_id: "q1" },
    });
    post.mockResolvedValue(ok(interview({})));
    await apiInterviewClient.askAgain("me");
  });

  it("at the limit, leaves keeping going to the member rather than asking by itself", async () => {
    const post = vi.spyOn(api, "POST");
    vi.spyOn(api, "GET").mockResolvedValue(
      ok(interview({ question: null, at_limit: true, needs_more: true })),
    );
    await expect(apiInterviewClient.current()).resolves.toMatchObject({ stage: "notEnough" });
    expect(post).not.toHaveBeenCalled();
  });

  it("carries what a rewrite did to the book", async () => {
    vi.spyOn(api, "POST").mockResolvedValue(
      ok({
        title: "T",
        author_name: "A",
        blurb: null,
        status: "draft",
        rewrite_unchanged: true,
        chapters: [{ id: "1", title: "C", summary: "S", quotes: [], has_previous: true }],
      }),
    );
    await expect(apiInterviewClient.rewriteChapter("me", "1")).resolves.toMatchObject({
      book: { rewriteUnchanged: true, chapters: [{ hasPrevious: true }] },
    });
  });

  it("reads the writing stages after a refresh", async () => {
    vi.spyOn(api, "GET")
      .mockResolvedValueOnce(ok({ ...interview({ question: null }), stage: "drafting" }))
      .mockResolvedValueOnce(ok({ ...interview({ question: null }), stage: "finishing" }));
    await expect(apiInterviewClient.current()).resolves.toMatchObject({ stage: "drafting", about: "titles" });
    await expect(apiInterviewClient.current()).resolves.toMatchObject({ stage: "drafting", about: "book" });
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
