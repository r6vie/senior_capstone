import type { LinkedInLoginResponse, LoginResponse, Profile, ProfileInput, User } from "./types";

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

async function request<T>(path: string, options: RequestInit = {}, token?: string | null): Promise<T> {
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
        "The backend could not reach MongoDB. Check that FastAPI is running and Atlas allows this network.",
      );
    }
    throw new ApiError(response.status, errorMessage(payload));
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  linkedInExchange: (code: string) =>
    request<LinkedInLoginResponse>("/auth/linkedin/exchange", { method: "POST", body: JSON.stringify({ code }) }),
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
};
