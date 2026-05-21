"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type AuthUser = {
  email?: string;
  name?: string;
  username?: string;
};

type AuthContextValue = {
  isAuthenticated: boolean;
  signIn: (user: AuthUser) => void;
  signOut: () => void;
  user: AuthUser | null;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);

  const signIn = useCallback((nextUser: AuthUser) => {
    setUser(nextUser);
  }, []);

  const signOut = useCallback(() => {
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      isAuthenticated: user !== null,
      signIn,
      signOut,
      user,
    }),
    [signIn, signOut, user]
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
