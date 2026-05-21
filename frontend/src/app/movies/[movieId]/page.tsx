import { PageSection } from "@/components/ui/PageSection";
import { StateMessage } from "@/components/ui/StateMessage";

export default function MovieDetailPage() {
  return (
    <PageSection
      description="Veja sinopse, duração, gêneros e sessões disponíveis para o filme selecionado."
      eyebrow="Filme"
      title="Detalhes do filme"
    >
      <StateMessage title="Filme não carregado">
        Os detalhes serão buscados no catálogo público quando a integração da
        página for implementada.
      </StateMessage>
    </PageSection>
  );
}
