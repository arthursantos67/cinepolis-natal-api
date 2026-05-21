import Link from "next/link";

import { PageSection } from "@/components/ui/PageSection";
import { StateMessage } from "@/components/ui/StateMessage";

export default function RegisterPage() {
  return (
    <PageSection
      description="Cadastre-se para comprar ingressos, acompanhar pedidos e acessar suas reservas."
      eyebrow="Autenticação"
      title="Criar conta"
    >
      <div className="panel">
        <form className="form-grid">
          <div className="form-field">
            <label htmlFor="username">Nome de usuário</label>
            <input
              autoComplete="username"
              id="username"
              name="username"
              placeholder="seu_nome"
              type="text"
            />
          </div>
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
              autoComplete="new-password"
              id="password"
              name="password"
              placeholder="Crie uma senha"
              type="password"
            />
          </div>
          <button className="button button-primary" type="button">
            Criar conta
          </button>
        </form>
      </div>
      <StateMessage title="Já possui cadastro?">
        <Link className="text-link" href="/login">
          Entrar na sua conta
        </Link>{" "}
        para continuar sua compra.
      </StateMessage>
    </PageSection>
  );
}
