"use client";

import { useCallback } from "react";

import { useRouter } from "next/navigation";

import { useAuth } from "@/contexts/AuthContext";
import {
  getBrowserCurrentPath,
  getGuardedActionDecision,
} from "./route-guards";

export function useGuardedAction() {
  const router = useRouter();
  const { isAuthenticated, status } = useAuth();

  return useCallback(
    (action: () => void) => {
      const decision = getGuardedActionDecision({
        currentPath: getBrowserCurrentPath(),
        isAuthenticated,
        status,
      });

      if (decision.allowed) {
        action();
        return true;
      }

      if (decision.loginUrl) {
        router.push(decision.loginUrl);
      }

      return false;
    },
    [isAuthenticated, router, status]
  );
}
