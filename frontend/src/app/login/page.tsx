import Link from "next/link";

import { LoginForm } from "@/components/auth/LoginForm";
import { PageSection } from "@/components/ui/PageSection";
import { StateMessage } from "@/components/ui/StateMessage";

export default function LoginPage() {
  return (
    <PageSection
      description="Acesse sua conta para reservar assentos, finalizar compras e consultar ingressos."
      eyebrow="Autenticação"
      title="Entrar"
    >
      <LoginForm />
      <StateMessage title="Ainda não tem conta?">
        <Link className="text-link" href="/register">
          Criar uma conta
        </Link>{" "}
        para acompanhar seus ingressos e compras.
      </StateMessage>
    </PageSection>
  );
}
