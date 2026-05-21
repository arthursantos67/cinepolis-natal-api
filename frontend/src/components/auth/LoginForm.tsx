"use client";

import { useState, type FormEvent } from "react";

import { useRouter } from "next/navigation";

import { getApiErrorUserMessage, sanitizeRedirectPath } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";

function getRedirectPath() {
  if (typeof window === "undefined") {
    return "/";
  }

  const redirect = new URLSearchParams(window.location.search).get("redirect");
  return redirect ? sanitizeRedirectPath(redirect) : "/";
}

export function LoginForm() {
  const router = useRouter();
  const { loading, login } = useAuth();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);

    const formData = new FormData(event.currentTarget);
    const email = String(formData.get("email") ?? "");
    const password = String(formData.get("password") ?? "");

    try {
      await login({ email, password });
      router.replace(getRedirectPath());
    } catch (error) {
      setErrorMessage(getApiErrorUserMessage(error));
    }
  }

  return (
    <div className="panel">
      <form className="form-grid" onSubmit={handleSubmit}>
        <div className="form-field">
          <label htmlFor="email">E-mail</label>
          <input
            autoComplete="email"
            id="email"
            name="email"
            placeholder="voce@email.com"
            required
            type="email"
          />
        </div>
        <div className="form-field">
          <label htmlFor="password">Senha</label>
          <input
            autoComplete="current-password"
            id="password"
            name="password"
            placeholder="Sua senha"
            required
            type="password"
          />
        </div>
        {errorMessage ? (
          <p className="form-error" role="alert">
            {errorMessage}
          </p>
        ) : null}
        <button className="button button-primary" disabled={loading} type="submit">
          {loading ? "Entrando..." : "Entrar"}
        </button>
      </form>
    </div>
  );
}
