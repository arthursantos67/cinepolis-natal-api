import { buildLoginRedirectUrl } from "@/api/client";
import type { AuthStatus } from "@/contexts/auth-state";

export const PROTECTED_ROUTES = [
  "/ticket-types",
  "/checkout",
  "/confirmation",
  "/my-tickets",
] as const;

type ProtectedRouteDecision = {
  renderContent: boolean;
  redirectToLogin: boolean;
};

type GuardedActionDecision =
  | {
      allowed: true;
      loginUrl: null;
      pending: false;
    }
  | {
      allowed: false;
      loginUrl: string;
      pending: false;
    }
  | {
      allowed: false;
      loginUrl: null;
      pending: true;
    };

type AuthGateInput = {
  isAuthenticated: boolean;
  status: AuthStatus;
};

type LocationParts = {
  hash?: string;
  pathname: string;
  search?: string;
};

export function isProtectedRoute(pathname: string) {
  return PROTECTED_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`)
  );
}

export function getProtectedRouteDecision({
  isAuthenticated,
  status,
}: AuthGateInput): ProtectedRouteDecision {
  if (isAuthenticated) {
    return {
      redirectToLogin: false,
      renderContent: true,
    };
  }

  return {
    redirectToLogin: status !== "loading",
    renderContent: false,
  };
}

export function getGuardedActionDecision({
  currentPath,
  isAuthenticated,
  status,
}: AuthGateInput & { currentPath: string }): GuardedActionDecision {
  if (isAuthenticated) {
    return {
      allowed: true,
      loginUrl: null,
      pending: false,
    };
  }

  if (status === "loading") {
    return {
      allowed: false,
      loginUrl: null,
      pending: true,
    };
  }

  return {
    allowed: false,
    loginUrl: buildLoginRedirectUrl(currentPath),
    pending: false,
  };
}

export function buildCurrentInternalPath({
  hash = "",
  pathname,
  search = "",
}: LocationParts) {
  return `${pathname}${search}${hash}`;
}

export function getBrowserCurrentPath() {
  if (typeof window === "undefined") {
    return "/";
  }

  return buildCurrentInternalPath(window.location);
}
