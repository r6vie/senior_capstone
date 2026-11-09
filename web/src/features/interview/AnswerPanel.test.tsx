import { act, fireEvent, render, screen } from "@testing-library/react";
import { AnswerPanel } from "./AnswerPanel";

// A stand-in for the browser's speech recognition, driven by hand.
class FakeRecognition {
  static instances: FakeRecognition[] = [];
  continuous = false;
  interimResults = false;
  lang = "";
  onresult: ((event: unknown) => void) | null = null;
  onerror: ((event: { error: string }) => void) | null = null;
  onend: (() => void) | null = null;
  constructor() {
    FakeRecognition.instances.push(this);
  }
  start() {}
  stop() {
    this.onend?.();
  }
  abort() {}
  say(transcript: string, isFinal = true) {
    act(() => {
      this.onresult?.({ resultIndex: 0, results: [Object.assign({ isFinal }, { 0: { transcript } })] });
    });
  }
  die() {
    act(() => this.onend?.());
  }
}

function microphone(): FakeRecognition {
  const latest = FakeRecognition.instances.at(-1);
  if (!latest) throw new Error("Nothing is listening.");
  return latest;
}

function field() {
  return screen.getByLabelText("Your answer") as HTMLTextAreaElement;
}

function click(name: string | RegExp) {
  fireEvent.click(screen.getByRole("button", { name }));
}

describe("AnswerPanel with the microphone", () => {
  beforeEach(() => {
    localStorage.clear();
    FakeRecognition.instances = [];
    vi.stubGlobal("SpeechRecognition", FakeRecognition);
    render(<AnswerPanel draftKey="draft" busy={false} onSend={() => {}} onSkip={() => {}} />);
  });
  afterEach(() => vi.unstubAllGlobals());

  it("adds what was said after what was typed", () => {
    fireEvent.change(field(), { target: { value: "Three paragraphs I typed." } });
    click(/Speak/);
    microphone().say("One more thought.");
    click("Stop");
    expect(field().value).toBe("Three paragraphs I typed.\n\nOne more thought.");
  });

  it("leaves typed words alone when nothing was heard", () => {
    fireEvent.change(field(), { target: { value: "Three paragraphs I typed." } });
    click(/Speak/);
    click("Stop");
    expect(field().value).toBe("Three paragraphs I typed.");
    expect(screen.getByRole("button", { name: /Speak/ })).toBeTruthy();
  });

  it("Record again replaces only the last recording", () => {
    fireEvent.change(field(), { target: { value: "Typed." } });
    click(/Speak/);
    microphone().say("First try.");
    click("Stop");
    click(/Record again/);
    microphone().say("Second try.");
    click("Stop");
    expect(field().value).toBe("Typed.\n\nSecond try.");
  });

  it("Record again keeps a recording the member has since edited", () => {
    click(/Speak/);
    microphone().say("First try.");
    click("Stop");
    fireEvent.change(field(), { target: { value: "First try, fixed by hand" } });
    click(/Record again/);
    microphone().say("Second try.");
    click("Stop");
    expect(field().value).toBe("First try, fixed by hand\n\nSecond try.");
  });

  it("Cancel keeps what was typed", () => {
    fireEvent.change(field(), { target: { value: "Typed." } });
    click(/Speak/);
    microphone().say("Never mind.");
    click("Cancel");
    expect(field().value).toBe("Typed.");
  });

  it("shows the words as they're heard, with no made-up levels", () => {
    click(/Speak/);
    microphone().say("Words so far", false);
    expect(screen.getByText("Words so far")).toBeTruthy();
    expect(screen.getByText(/Speak naturally/)).toBeTruthy();
    expect(document.querySelector(".iv-wave")).toBeNull();
  });

  it("puts a space between final results", () => {
    click(/Speak/);
    microphone().say("One.");
    microphone().say("Two.");
    click("Stop");
    expect(field().value).toBe("One. Two.");
  });

  it("keeps listening when the browser ends recognition by itself, without losing words", () => {
    click(/Speak/);
    microphone().say("Before the gap.");
    const first = microphone();
    first.die();
    expect(microphone()).not.toBe(first);
    expect(screen.getByRole("button", { name: "Stop" })).toBeTruthy();
    microphone().say("After the gap.");
    click("Stop");
    expect(field().value).toBe("Before the gap. After the gap.");
  });

  it("says so when the microphone really has stopped, and keeps what it heard", () => {
    click(/Speak/);
    microphone().say("What I got out.");
    for (let i = 0; i < 4; i++) microphone().die();
    expect(field().value).toBe("What I got out.");
    expect(screen.getByText("The microphone stopped. Here's what I heard.")).toBeTruthy();
  });

  it("keeps what was heard when an error stops recording", () => {
    click(/Speak/);
    microphone().say("Heard this much.");
    act(() => {
      microphone().onerror?.({ error: "network" });
      microphone().onend?.();
    });
    expect(field().value).toBe("Heard this much.");
    expect(screen.getByText(/Speech recognition needs a connection/)).toBeTruthy();
  });
});
