import { PageSection } from "@/components/ui/PageSection";
import { StateMessage } from "@/components/ui/StateMessage";

export default function SeatSelectionPage() {
  return (
    <PageSection
      description="Escolha assentos disponíveis, acompanhe reservas temporárias e avance para os tipos de ingresso."
      eyebrow="Sessão"
      title="Seleção de assentos"
    >
      <div className="panel">
        <span className="inline-status inline-status-info">Tela</span>
        <p className="panel-copy">
          O mapa de assentos usará estados visuais para disponível, selecionado,
          reservado, comprado e acessível.
        </p>
      </div>
      <StateMessage tone="loading" title="Mapa de assentos pendente">
        A estrutura responsiva permite rolagem horizontal quando a sala for mais
        larga que a tela do dispositivo.
      </StateMessage>
    </PageSection>
  );
}
