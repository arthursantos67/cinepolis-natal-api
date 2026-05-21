"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { useRouter } from "next/navigation";

import { authApi, type LoginCredentials } from "@/api/auth";
import {
  buildLoginRedirectUrl,
  sanitizeRedirectPath,
  setApiAuthController,
} from "@/api/client";
import {
  applyAccessRefresh,
  applyCurrentUser,
  applyLogin,
  applyLogout,
  initialAuthState,
  isAuthenticated as getIsAuthenticated,
  startAuthLoading,
  type AuthState,
  type AuthUser,
} from "./auth-state";

export type { AuthUser } from "./auth-state";

export const AUTH_PROTECTED_STATE_RESET_EVENT =
  "cinepolis:protected-state-reset";

type AuthContextValue = {
  accessToken: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (credentials: LoginCredentials) => Promise<AuthUser>;
  logout: (options?: { redirectToLogin?: boolean }) => void;
  refreshAccessToken: () => Promise<string | null>;
  refreshToken: string | null;
  reloadCurrentUser: () => Promise<AuthUser>;
  signOut: () => void;
  status: AuthState["status"];
  user: AuthUser | null;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [state, setState] = useState<AuthState>(initialAuthState);
  const accessTokenRef = useRef<string | null>(null);
  const refreshTokenRef = useRef<string | null>(null);
  const refreshPromiseRef = useRef<Promise<string | null> | null>(null);

  const clearProtectedState = useCallback(() => {
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent(AUTH_PROTECTED_STATE_RESET_EVENT));
    }
  }, []);

  const clearAuthState = useCallback(() => {
    accessTokenRef.current = null;
    refreshTokenRef.current = null;
    setState(applyLogout());
    clearProtectedState();
  }, [clearProtectedState]);

  const redirectToLogin = useCallback(() => {
    if (typeof window === "undefined") {
      return;
    }

    const currentPath = `${window.location.pathname}${window.location.search}${window.location.hash}`;
    router.replace(buildLoginRedirectUrl(currentPath));
  }, [router]);

  const logout = useCallback(
    ({ redirectToLogin: shouldRedirect = false } = {}) => {
      clearAuthState();

      if (shouldRedirect) {
        redirectToLogin();
      }
    },
    [clearAuthState, redirectToLogin]
  );

  const reloadCurrentUser = useCallback(async () => {
    setState((currentState) => startAuthLoading(currentState));
    const user = await authApi.currentUser();
    setState((currentState) => applyCurrentUser(currentState, user));
    return user;
  }, []);

  const refreshAccessToken = useCallback(async () => {
    if (refreshPromiseRef.current) {
      return refreshPromiseRef.current;
    }

    const refreshToken = refreshTokenRef.current;

    if (!refreshToken) {
      clearAuthState();
      return null;
    }

    refreshPromiseRef.current = authApi
      .refreshAccess(refreshToken)
      .then(({ access }) => {
        accessTokenRef.current = access;
        setState((currentState) => applyAccessRefresh(currentState, access));
        return access;
      })
      .catch((error) => {
        clearAuthState();
        throw error;
      })
      .finally(() => {
        refreshPromiseRef.current = null;
      });

    return refreshPromiseRef.current;
  }, [clearAuthState]);

  const login = useCallback(async (credentials: LoginCredentials) => {
    setState((currentState) => startAuthLoading(currentState));

    try {
      const tokens = await authApi.login(credentials);
      accessTokenRef.current = tokens.access;
      refreshTokenRef.current = tokens.refresh;
      setState((currentState) => applyLogin(currentState, tokens));

      const user = await authApi.currentUser(tokens.access);
      setState((currentState) => applyCurrentUser(currentState, user));
      return user;
    } catch (error) {
      clearAuthState();
      throw error;
    }
  }, [clearAuthState]);

  useEffect(() => {
    accessTokenRef.current = state.accessToken;
    refreshTokenRef.current = state.refreshToken;
  }, [state.accessToken, state.refreshToken]);

  useEffect(() => {
    setApiAuthController({
      getAccessToken: () => accessTokenRef.current,
      handleRefreshFailure: () => {
        clearAuthState();
        redirectToLogin();
      },
      refreshAccessToken,
    });

    return () => {
      setApiAuthController(null);
    };
  }, [clearAuthState, redirectToLogin, refreshAccessToken]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const redirect = new URLSearchParams(window.location.search).get("redirect");

    if (state.status === "authenticated" && redirect) {
      router.replace(sanitizeRedirectPath(redirect));
    }
  }, [router, state.status]);

  const value = useMemo(
    () => ({
      accessToken: state.accessToken,
      isAuthenticated: getIsAuthenticated(state),
      loading: state.status === "loading",
      login,
      logout,
      refreshAccessToken,
      refreshToken: state.refreshToken,
      reloadCurrentUser,
      signOut: logout,
      status: state.status,
      user: state.user,
    }),
    [login, logout, refreshAccessToken, reloadCurrentUser, state]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth deve ser usado dentro de AuthProvider.");
  }

  return context;
}
