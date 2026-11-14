import { apiRequest, setAuthToken, removeAuthToken, getAuthToken } from './client';

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserProfile {
  user_id: number;
  name: string;
  email: string;
  notification_pref: string;
  consent_given_at: string;
  created_at: string;
}

export async function loginWithCredentials(
  usernameOrEmail: string,
  password: string
): Promise<LoginResponse> {
  const isEmail = usernameOrEmail.includes('@');
  const payload = isEmail
    ? { email: usernameOrEmail, password }
    : { username: usernameOrEmail, password };

  const res = await apiRequest<LoginResponse>('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  setAuthToken(res.access_token);
  return res;
}

export async function loginWithGoogle(
  email?: string,
  name?: string
): Promise<LoginResponse> {
  const res = await apiRequest<LoginResponse>('/auth/google', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: email || 'tejas.google@vault.local',
      name: name || 'Tejas (Google)',
    }),
  });

  setAuthToken(res.access_token);
  return res;
}

export async function getCurrentUser(): Promise<UserProfile> {
  return apiRequest<UserProfile>('/auth/me');
}

export function logout(): void {
  removeAuthToken();
}

export function isAuthenticated(): boolean {
  return !!getAuthToken();
}
