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
