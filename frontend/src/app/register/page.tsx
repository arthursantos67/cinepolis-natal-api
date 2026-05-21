import Link from "next/link";

import { RegisterForm } from "@/components/auth/RegisterForm";
import { PageSection } from "@/components/ui/PageSection";
import { StateMessage } from "@/components/ui/StateMessage";

export default function RegisterPage() {
  return (
    <PageSection
      description="Cadastre-se para comprar ingressos, acompanhar pedidos e acessar suas reservas."
      eyebrow="Autenticação"
      title="Criar conta"
    >
      <RegisterForm />
      <StateMessage title="Já possui cadastro?">
        <Link className="text-link" href="/login">
          Entrar na sua conta
        </Link>{" "}
        para continuar sua compra.
      </StateMessage>
    </PageSection>
  );
}
