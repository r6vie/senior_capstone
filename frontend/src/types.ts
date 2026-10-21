export interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
}

export interface ProfileInput {
  name: string;
  affiliation: string;
  location: string;
  expertise: string[];
  interests: string[];
  role: "student" | "alumni";
  industry: string;
  background: string;
  help_offered: string[];
  help_needed: string[];
  availability: "available" | "limited" | "unavailable";
  meeting_preference: "remote" | "in_person" | "either";
  graduation_year: number | null;
}

export interface Profile extends ProfileInput {
  id: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
}

export interface MatchSearchInput {
  query: string;
  industry?: string;
  location?: string;
  meeting_preference?: ProfileInput["meeting_preference"];
  limit?: number;
}

export interface MatchResult {
  profile: Profile;
  score: number;
  reasons: string[];
  score_breakdown: Record<string, number>;
}
