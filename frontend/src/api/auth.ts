import { apiRequest } from "./client";

export type LoginCredentials = {
  email: string;
  password: string;
};

export type LoginResponse = {
  access: string;
  refresh: string;
};

export type CurrentUserResponse = {
  created_at: string;
  email: string;
  id: string;
  username: string;
};

export type RefreshAccessResponse = {
  access: string;
};

export const authApi = {
  login(credentials: LoginCredentials) {
    return apiRequest<LoginResponse>("/api/v1/auth/login/", {
      auth: "none",
      json: credentials,
      method: "POST",
    });
  },

  currentUser(accessToken?: string) {
    return apiRequest<CurrentUserResponse>("/api/v1/users/me/", {
      auth: accessToken ? "none" : "required",
      token: accessToken,
    });
  },

  refreshAccess(refreshToken: string) {
    return apiRequest<RefreshAccessResponse>("/api/v1/auth/token/refresh/", {
      auth: "none",
      json: { refresh: refreshToken },
      method: "POST",
    });
  },
};
