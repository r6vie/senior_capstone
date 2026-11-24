import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MeetingPage } from "./MeetingPage";

const api = vi.hoisted(() => ({ GET: vi.fn(), PUT: vi.fn() }));
vi.mock("../../api/client", () => ({ api }));

const day = (days: number, hour = 15, minute = 0) => {
  const date = new Date();
  date.setDate(date.getDate() + days);
  date.setHours(hour, minute, 0, 0);
  return date;
};

const meeting = {
  checkout_id: "c1",
  book_title: "Maya's book",
  other_name: "Maya Lee",
  minutes: 30,
  my_times: [] as string[],
  their_times: [] as string[],
  shared_times: [] as string[],
  start: null as string | null,
  video_link: null as string | null,
  place_note: null as string | null,
};

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/checkouts/c1/meeting"]}>
      <Routes>
        <Route path="/checkouts/:checkoutId/meeting" element={<MeetingPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.resetAllMocks();
  api.GET.mockResolvedValue({ data: meeting });
});

describe("MeetingPage", () => {
  it("offers to try again when loading fails, including a dropped connection", async () => {
    api.GET.mockResolvedValueOnce({ error: { detail: "Unavailable" }, response: { status: 503 } });
    renderPage();
    expect((await screen.findByRole("alert")).textContent).toContain("couldn't load this meeting");
    expect(screen.queryByText(/couldn't find this meeting/)).toBeNull();

    api.GET.mockRejectedValueOnce(new TypeError("Failed to fetch"));
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect((await screen.findByRole("alert")).textContent).toContain("couldn't load this meeting");

    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Meeting Maya Lee" })).toBeTruthy();
  });

  it("says the connection dropped when confirming a time, rather than staying stuck", async () => {
    const time = day(3).toISOString();
    api.GET.mockResolvedValue({
      data: { ...meeting, my_times: [time], their_times: [time], shared_times: [time] },
    });
    api.PUT.mockRejectedValue(new TypeError("Failed to fetch"));
    renderPage();
    fireEvent.click((await screen.findAllByRole("button", { name: /^Confirm / }))[0] as HTMLElement);
    expect((await screen.findByRole("alert")).textContent).toContain("couldn't reach Trove");
  });

  it("names the other person and starts with nothing to pick", async () => {
    renderPage();
    expect(await screen.findByRole("heading", { level: 1, name: "Meeting Maya Lee" })).toBeTruthy();
    expect(screen.getByText(/No times yet/)).toBeTruthy();
    expect(screen.getByText(/Nothing to pick yet/)).toBeTruthy();
    const save = screen.getByRole("button", { name: "Save my times" }) as HTMLButtonElement;
    expect(save.disabled).toBe(true);
    expect(screen.getByRole("link", { name: /Back to Checkouts/ }).getAttribute("href")).toBe("/checkouts");
  });

  it("once a time is confirmed, keeps changing it behind a button and moves focus to the new time", async () => {
    const first = day(3).toISOString();
    const second = day(4).toISOString();
    api.GET.mockResolvedValue({
      data: {
        ...meeting,
        start: first,
        my_times: [first, second],
        their_times: [first, second],
        shared_times: [first, second],
      },
    });
    renderPage();

    await screen.findByText("Confirmed");
    expect(screen.getByRole("link", { name: /Back to Checkouts/ })).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "Times that work for you" })).toBeNull();
    expect(screen.queryByRole("heading", { name: "Change the time" })).toBeNull();

    const toggle = screen.getByRole("button", { name: "Change the time" });
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(toggle);
    expect(toggle.getAttribute("aria-expanded")).toBe("true");
    expect(toggle.textContent).toBe("Keep this time");
    expect(screen.getByRole("heading", { name: "Times that work for you" })).toBeTruthy();

    api.PUT.mockResolvedValue({
      data: {
        ...meeting,
        start: second,
        my_times: [first, second],
        their_times: [first, second],
        shared_times: [first, second],
      },
    });
    fireEvent.click(screen.getAllByRole("button", { name: /^Confirm / })[1] as HTMLElement);

    await waitFor(() =>
      expect(screen.queryByRole("heading", { name: "Times that work for you" })).toBeNull(),
    );
    await waitFor(() => expect(document.activeElement?.id).toBe("confirmed-heading"));
    expect(screen.getByRole("button", { name: "Change the time" }).getAttribute("aria-expanded")).toBe(
      "false",
    );
  });

  it("keeps the details form open until there are details, then behind an edit button", async () => {
    const start = day(3).toISOString();
    api.GET.mockResolvedValue({ data: { ...meeting, start } });
    renderPage();

    await screen.findByText("Confirmed");
    expect(screen.queryByRole("button", { name: "Edit where you'll meet" })).toBeNull();
    api.PUT.mockResolvedValue({ data: { ...meeting, start, video_link: "https://meet.example.com/abc" } });
    fireEvent.change(screen.getByLabelText(/^Video link/), {
      target: { value: "https://meet.example.com/abc" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save meeting details" }));

    expect(await screen.findByRole("link", { name: "Open the video link" })).toBeTruthy();
    expect(screen.queryByLabelText(/^Video link/)).toBeNull();
    await waitFor(() => expect(document.activeElement?.id).toBe("confirmed-heading"));

    fireEvent.click(screen.getByRole("button", { name: "Edit where you'll meet" }));
    expect((screen.getByLabelText(/^Video link/) as HTMLInputElement).value).toBe(
      "https://meet.example.com/abc",
    );
    fireEvent.click(screen.getByRole("button", { name: "Stop editing" }));
    expect(screen.queryByLabelText(/^Video link/)).toBeNull();
  });

  it("adds a time, saves it, and sends it as an exact instant", async () => {
    const time = day(3);
    api.PUT.mockResolvedValue({ data: { ...meeting, my_times: [time.toISOString()] } });
    renderPage();
    await screen.findByText(/No times yet/);

    const local = new Date(time.getTime() - time.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    fireEvent.change(screen.getByLabelText("Add a time"), { target: { value: local } });
    fireEvent.click(screen.getByRole("button", { name: "Add this time" }));
    fireEvent.click(screen.getByRole("button", { name: "Save my times" }));

    await screen.findByText("Your times are saved.");
    expect(api.PUT).toHaveBeenCalledWith("/meetings/{checkout_id}/times", {
      params: { path: { checkout_id: "c1" } },
      body: { times: [time.toISOString()] },
    });
  });

  it("refuses a time that isn't on the hour or half hour, and one that has passed", async () => {
    renderPage();
    await screen.findByText(/No times yet/);
    const field = screen.getByLabelText("Add a time");
    const asLocal = (date: Date) =>
      new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);

    fireEvent.change(field, { target: { value: asLocal(day(3, 15, 10)) } });
    fireEvent.click(screen.getByRole("button", { name: "Add this time" }));
    expect((await screen.findByRole("alert")).textContent).toMatch(/hour or the half hour/);

    fireEvent.change(field, { target: { value: asLocal(day(-1)) } });
    fireEvent.click(screen.getByRole("button", { name: "Add this time" }));
    await waitFor(() => expect(screen.getByRole("alert").textContent).toMatch(/passed/));
    expect(api.PUT).not.toHaveBeenCalled();
  });

  it("shows which times you both offered and confirms the one you choose", async () => {
    const both = day(3).toISOString();
    const theirs = day(4).toISOString();
    api.GET.mockResolvedValue({
      data: { ...meeting, my_times: [both], their_times: [both, theirs], shared_times: [both] },
    });
    api.PUT.mockResolvedValue({
      data: { ...meeting, start: both, my_times: [both], their_times: [both, theirs] },
    });
    renderPage();

    expect(await screen.findByText("You both offered this")).toBeTruthy();
    expect(screen.getByText("Maya Lee offered this")).toBeTruthy();
    fireEvent.click(screen.getAllByRole("button", { name: /^Confirm / })[0] as HTMLElement);

    await screen.findByText("Confirmed");
    expect(api.PUT).toHaveBeenCalledWith("/meetings/{checkout_id}/confirm", {
      params: { path: { checkout_id: "c1" } },
      body: { start: both },
    });
    expect(screen.getByText(/30 minutes with Maya Lee/)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Add to my calendar" })).toBeTruthy();
  });

  it("says so when nothing overlaps yet", async () => {
    api.GET.mockResolvedValue({
      data: { ...meeting, my_times: [day(3).toISOString()], their_times: [day(4).toISOString()] },
    });
    renderPage();
    expect(await screen.findByText(/None of your times overlap yet/)).toBeTruthy();
  });

  it("saves the video link and shows a reason when it is refused", async () => {
    renderPage();
    await screen.findByText(/Where you'll meet/);

    api.PUT.mockResolvedValue({
      error: {
        detail: [
          { loc: ["body", "video_link"], msg: "Value error, Enter a full link that starts with https://" },
        ],
      },
    });
    fireEvent.change(screen.getByLabelText(/^Video link/), { target: { value: "meet.example.com" } });
    fireEvent.click(screen.getByRole("button", { name: "Save meeting details" }));
    expect((await screen.findByRole("alert")).textContent).toContain(
      "Enter a full link that starts with https://",
    );

    api.PUT.mockResolvedValue({ data: { ...meeting, video_link: "https://meet.example.com/abc" } });
    fireEvent.change(screen.getByLabelText(/^Video link/), {
      target: { value: " https://meet.example.com/abc " },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save meeting details" }));
    await screen.findByText("Saved. Both of you can see this.");
    expect(api.PUT).toHaveBeenLastCalledWith("/meetings/{checkout_id}/details", {
      params: { path: { checkout_id: "c1" } },
      body: { video_link: "https://meet.example.com/abc", place_note: null },
    });
  });

  it("explains when the meeting can't be found", async () => {
    api.GET.mockResolvedValue({ error: { detail: "Checkout not found." }, response: { status: 404 } });
    renderPage();
    expect(await screen.findByText(/We couldn't find this meeting/)).toBeTruthy();
    expect(screen.getByRole("link", { name: "Back to Checkouts" })).toBeTruthy();
  });
});
