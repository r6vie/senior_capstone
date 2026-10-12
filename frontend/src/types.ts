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
}

export interface Profile extends ProfileInput {
  id: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
}

export type RequestType = "mentorship" | "career_advice" | "introduction" | "collaboration" | "other";

export interface RequestTypeOption {
  value: RequestType;
  label: string;
}

export interface Connection {
  id: string;
  status: "pending" | "accepted" | "declined";
  type: RequestType;
  direction: "incoming" | "outgoing";
  message: string | null;
  created_at: string;
  responded_at: string | null;
  profile: Profile | null;
  contact_email: string | null; // only set once accepted
}

export interface ThreadMessage {
  id: string;
  from_me: boolean;
  body: string;
  created_at: string;
}

