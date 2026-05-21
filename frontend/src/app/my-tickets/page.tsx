import { PageSection } from "@/components/ui/PageSection";
import { StateMessage } from "@/components/ui/StateMessage";

export default function MyTicketsPage() {
  return (
    <PageSection
      description="Consulte ingressos futuros e compras anteriores quando estiver autenticado."
      eyebrow="Conta"
      title="Meus ingressos"
    >
      <StateMessage title="Nenhum ingresso carregado">
        A lista de ingressos será conectada à conta do usuário.
      </StateMessage>
    </PageSection>
  );
}
