"use client";

import { useState } from "react";

import { useGuardedAction } from "@/components/auth/useGuardedAction";

export function SeatSelectionActions() {
  const guardAction = useGuardedAction();
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  function handleReserveAttempt() {
    guardAction(() => {
      setStatusMessage("Reserva autenticada pronta para integração com a API.");
    });
  }

  function handleReleaseAttempt() {
    guardAction(() => {
      setStatusMessage("Liberação autenticada pronta para integração com a API.");
    });
  }

  return (
    <div className="page-actions" aria-label="Ações de assento">
      <button
        className="button button-primary"
        onClick={handleReserveAttempt}
        type="button"
      >
        Reservar assento
      </button>
      <button
        className="button button-ghost"
        onClick={handleReleaseAttempt}
        type="button"
      >
        Liberar assento
      </button>
      {statusMessage ? (
        <p className="inline-status inline-status-info" role="status">
          {statusMessage}
        </p>
      ) : null}
    </div>
  );
}
