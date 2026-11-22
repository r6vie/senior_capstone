import { act, render, screen } from "@testing-library/react";
import { useState } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { LoadingGate, PageLoading } from "./Loading";

function Page({ ready }: { ready: boolean }) {
  return (
    <main>
      <h1>Checkouts</h1>
      {!ready && <PageLoading />}
    </main>
  );
}

let finish: () => void = () => undefined;
function Harness() {
  const [ready, setReady] = useState(false);
  finish = () => setReady(true);
  return (
    <LoadingGate>
      <Page ready={ready} />
    </LoadingGate>
  );
}

const root = () => document.querySelector(".loading-root") as HTMLElement;

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

describe("LoadingGate", () => {
  it("keeps the page hidden while it loads, and shows it all at once", async () => {
    render(<Harness />);
    expect(root().dataset.hidden).toBe("true");
    await act(async () => finish());
    expect(root().dataset.hidden).toBeUndefined();
  });

  it("shows no placeholder for a fast page", async () => {
    render(<Harness />);
    await act(async () => vi.advanceTimersByTime(150));
    expect(screen.queryByRole("status")).toBeNull();
    await act(async () => finish());
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("shows a still placeholder once a page is slow, and removes it when the page is ready", async () => {
    render(<Harness />);
    await act(async () => vi.advanceTimersByTime(250));
    expect(screen.getByRole("status").textContent).toBe("Loading");
    await act(async () => finish());
    expect(screen.queryByRole("status")).toBeNull();
    expect(root().dataset.hidden).toBeUndefined();
  });

  it("never hides the page for good", async () => {
    render(<Harness />);
    await act(async () => vi.advanceTimersByTime(10_001));
    expect(root().dataset.hidden).toBeUndefined();
  });

  it("shows a page with nothing to load straight away", async () => {
    render(
      <LoadingGate>
        <p>Sign in</p>
      </LoadingGate>,
    );
    await act(async () => undefined);
    expect(root().dataset.hidden).toBeUndefined();
  });
});
