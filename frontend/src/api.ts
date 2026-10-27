import type {
  BasicsForm, Fact, FactEdit, InterviewAnswer, InterviewTurn, LinkedInLoginResponse,
  LoginResponse, MatchResult, MeetingBrief, PracticeFeedback, ProfileAnswer,
  MatchSearchInput, OnboardingStatus, Profile, ProfileInput, User, Connection,
  RequestType, RequestTypeOption, ThreadMessage,
} from "./types";

const API_URL = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ?? "/api";

// A normal link (not fetch): the browser leaves for LinkedIn and returns through the backend.
export const LINKEDIN_START_URL = `${API_URL}/auth/linkedin/start`;

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function errorMessage(payload: unknown): string {
  if (!payload || typeof payload !== "object" || !("detail" in payload)) {
    return "Something went wrong. Please try again.";
  }

  const detail = (payload as { detail: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (!item || typeof item !== "object") return "Invalid information.";
        const issue = item as { loc?: unknown[]; msg?: string };
        const field = issue.loc?.at(-1);
        return `${typeof field === "string" ? `${field}: ` : ""}${issue.msg ?? "Invalid value."}`;
      })
      .join(" ");
  }
  return "Something went wrong. Please try again.";
}

async function request<T>(path: string, options: RequestInit = {}, token?: string | null, as: "json" | "text" = "json"): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...options, headers });
  } catch {
    throw new ApiError(0, "The backend is unavailable. Make sure it is running on port 8000.");
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    if (!payload && response.status >= 500) {
      throw new ApiError(
        response.status,
        "The backend is not running. Start FastAPI on port 8000, then try again.",
      );
    }
    throw new ApiError(response.status, errorMessage(payload));
  }

  if (response.status === 204) return undefined as T;
  return (as === "text" ? response.text() : response.json()) as Promise<T>;
}

export const api = {
  linkedInExchange: (code: string) =>
    request<LinkedInLoginResponse>("/auth/linkedin/exchange", { method: "POST", body: JSON.stringify({ code }) }),
  signup: (name: string, email: string, password: string) =>
    request<User>("/auth/signup", { method: "POST", body: JSON.stringify({ name, email, password }) }),
  login: (email: string, password: string) =>
    request<LoginResponse>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  me: (token: string) => request<User>("/auth/me", {}, token),
  logout: (token: string) => request<void>("/auth/logout", { method: "POST" }, token),
  profiles: (token: string, expertise = "") =>
    request<Profile[]>(`/profiles${expertise ? `?expertise=${encodeURIComponent(expertise)}` : ""}`, {}, token),
  myProfile: (token: string) => request<Profile>("/profiles/me", {}, token),
  createProfile: (token: string, profile: ProfileInput) =>
    request<Profile>("/profiles", { method: "POST", body: JSON.stringify(profile) }, token),
  updateProfile: (token: string, id: string, profile: Partial<ProfileInput>) =>
    request<Profile>(`/profiles/${id}`, { method: "PATCH", body: JSON.stringify(profile) }, token),
  deleteProfile: (token: string, id: string) =>
    request<void>(`/profiles/${id}`, { method: "DELETE" }, token),
  searchMatches: (token: string, search: MatchSearchInput) =>
    request<MatchResult[]>("/matches/search", { method: "POST", body: JSON.stringify(search) }, token),
  recommendedMatches: (token: string, limit = 6) =>
    request<MatchResult[]>(`/matches/recommended?limit=${limit}`, {}, token),
  meetingBrief: (token: string, profileId: string, goal: string) =>
    request<MeetingBrief>(`/meeting-prep/${profileId}`, { method: "POST", body: JSON.stringify({ goal }) }, token),
  askProfile: (token: string, profileId: string, goal: string, question: string) =>
    request<ProfileAnswer>(`/meeting-prep/${profileId}/ask`, { method: "POST", body: JSON.stringify({ goal, question }) }, token),
  practiceMeeting: (token: string, profileId: string, goal: string, answer: string, turn: number) =>
    request<PracticeFeedback>(`/meeting-prep/${profileId}/practice`, { method: "POST", body: JSON.stringify({ goal, answer, turn }) }, token),
  onboardingStatus: (token: string) => request<OnboardingStatus>("/onboarding/status", {}, token),
  submitBasics: (token: string, basics: BasicsForm) =>
    request<OnboardingStatus>("/onboarding/basics", { method: "POST", body: JSON.stringify(basics) }, token),
  currentInterview: (token: string) => request<InterviewTurn>("/interview/sessions/current", {}, token),
  startInterview: (token: string) => request<InterviewTurn>("/interview/sessions", { method: "POST" }, token),
  answerInterview: (token: string, sessionId: string, answer: InterviewAnswer) =>
    request<InterviewTurn>(`/interview/sessions/${sessionId}/answers`, { method: "POST", body: JSON.stringify(answer) }, token),
  finishInterview: (token: string, sessionId: string) =>
    request<InterviewTurn>(`/interview/sessions/${sessionId}/finish`, { method: "POST" }, token),
  myFacts: (token: string) => request<Fact[]>("/me/facts", {}, token),
  editFact: (token: string, id: string, edit: FactEdit) =>
    request<Fact>(`/me/facts/${id}`, { method: "PATCH", body: JSON.stringify(edit) }, token),
  deleteFact: (token: string, id: string) => request<void>(`/me/facts/${id}`, { method: "DELETE" }, token),
  myProfileMarkdown: (token: string) => request<string>("/me/profile.md", {}, token, "text"),
  // Connection requests
  requestTypes: (token: string) => request<RequestTypeOption[]>("/connections/types", {}, token),
  sendRequest: (token: string, profileId: string, type: RequestType, message: string) =>
    request<Connection>(
      "/connections",
      { method: "POST", body: JSON.stringify({ profile_id: profileId, type, message }) },
      token,
    ),
  connections: (token: string) => request<Connection[]>("/connections", {}, token),
  respond: (token: string, id: string, status: "accepted" | "declined") =>
    request<Connection>(`/connections/${id}`, { method: "PATCH", body: JSON.stringify({ status }) }, token),
  messages: (token: string, id: string) => request<ThreadMessage[]>(`/connections/${id}/messages`, {}, token),
  sendMessage: (token: string, id: string, body: string) =>
    request<ThreadMessage>(`/connections/${id}/messages`, { method: "POST", body: JSON.stringify({ body }) }, token),
};
