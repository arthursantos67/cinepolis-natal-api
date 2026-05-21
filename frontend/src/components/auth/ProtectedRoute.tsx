"use client";

import { useEffect, type ReactNode } from "react";

import { useRouter } from "next/navigation";

import { buildLoginRedirectUrl } from "@/api/client";
import { StateMessage } from "@/components/ui/StateMessage";
import { useAuth } from "@/contexts/AuthContext";
import {
  getBrowserCurrentPath,
  getProtectedRouteDecision,
} from "./route-guards";

type ProtectedRouteProps = {
  children: ReactNode;
};

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const router = useRouter();
  const { isAuthenticated, status } = useAuth();
  const decision = getProtectedRouteDecision({ isAuthenticated, status });

  useEffect(() => {
    if (decision.redirectToLogin) {
      router.replace(buildLoginRedirectUrl(getBrowserCurrentPath()));
    }
  }, [decision.redirectToLogin, router]);

  if (decision.renderContent) {
    return children;
  }

  return (
    <StateMessage tone="loading" title="Verificando acesso">
      Aguarde enquanto confirmamos sua sessão.
    </StateMessage>
  );
}
