import Link from "next/link";

import { PageSection } from "@/components/ui/PageSection";
import { StateMessage } from "@/components/ui/StateMessage";

export default function LoginPage() {
  return (
    <PageSection
      description="Acesse sua conta para reservar assentos, finalizar compras e consultar ingressos."
      eyebrow="Autenticação"
      title="Entrar"
    >
      <div className="panel">
        <form className="form-grid">
          <div className="form-field">
            <label htmlFor="email">E-mail</label>
            <input
              autoComplete="email"
              id="email"
              name="email"
              placeholder="voce@email.com"
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
              type="password"
            />
          </div>
          <button className="button button-primary" type="button">
            Entrar
          </button>
        </form>
      </div>
      <StateMessage title="Ainda não tem conta?">
        <Link className="text-link" href="/register">
          Criar uma conta
        </Link>{" "}
        para acompanhar seus ingressos e compras.
      </StateMessage>
    </PageSection>
  );
}
