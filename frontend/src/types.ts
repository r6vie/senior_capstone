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

export type Role = "student" | "alum" | "faculty" | "staff" | "other";
export type Seeking = "get_help" | "give_help" | "both";
export type FactKind = "need" | "offer" | "experience" | "background" | "goal" | "preference" | "availability" | "other";
export type Visibility = "public" | "matches_only" | "private";

export interface BasicsForm {
  role: Role;
  school: string;
  grad_year: number | null;
  majors: string[];
  seeking: Seeking;
  location: string;
}

export interface Fact {
  id: string;
  kind: FactKind;
  topic: string;
  text: string;
  detail: { key: string; value: string }[];
  links: string[];
  strength: number | null;
  visibility: Visibility;
  confirmed: boolean;
  confidence: number;
  source: "basics_form" | "interview" | "member_edit" | "resume";
  created_at: string;
  updated_at: string;
}

export interface FactEdit {
  text?: string;
  visibility?: Visibility;
  confirmed?: true;
}

export interface AreaCoverage {
  area: "needs" | "offers" | "style" | "background" | "goals";
  label: string;
  status: "missing" | "started" | "good";
  important: boolean;
}

export interface Coverage {
  percent: number;
  areas: AreaCoverage[];
}

export interface Question {
  id: string;
  area: AreaCoverage["area"];
  prompt: string;
  choices: string[];
  multiple: boolean;
  placeholder: string;
}

export interface InterviewAnswer {
  question_id: string;
  choices: string[];
  text: string;
  skipped?: boolean;
}

export interface InterviewTurn {
  interview: {
    session_id: string;
    status: "active" | "finished";
    question: Question | null;
    done: boolean;
    answered: number;
    added: string[];
    notice: string | null;
  };
  facts: Fact[];
  coverage: Coverage;
}

export interface OnboardingStatus {
  basics_done: boolean;
  basics: BasicsForm | null;
  open_interview_id: string | null;
  coverage: Coverage;
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

export interface LinkedInLoginResponse extends LoginResponse {
  is_new: boolean;
}
