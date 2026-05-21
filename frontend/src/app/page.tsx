import Link from "next/link";

import { PageSection } from "@/components/ui/PageSection";
import { StateMessage } from "@/components/ui/StateMessage";

export default function HomePage() {
  return (
    <PageSection
      actions={
        <>
          <Link className="button button-primary" href="#catalogo">
            Ver catálogo
          </Link>
          <Link className="button button-ghost" href="/login">
            Entrar
          </Link>
        </>
      }
      description="Encontre sessões em Natal, escolha seus assentos e avance para a compra de ingressos com uma experiência preparada para celular e desktop."
      eyebrow="Catálogo"
      title="Cinepolis Natal"
    >
      <div className="panel-grid" id="catalogo">
        <article className="panel">
          <span className="inline-status inline-status-success">Em breve</span>
          <h2 className="panel-title">Em cartaz</h2>
          <p className="panel-copy">
            Espaço reservado para os filmes disponíveis no catálogo público.
          </p>
        </article>
        <article className="panel">
          <span className="inline-status inline-status-info">Pré-venda</span>
          <h2 className="panel-title">Próximas sessões</h2>
          <p className="panel-copy">
            A base visual já está pronta para receber filmes em pré-venda.
          </p>
        </article>
        <article className="panel">
          <span className="inline-status inline-status-info">Ingressos</span>
          <h2 className="panel-title">Compra guiada</h2>
          <p className="panel-copy">
            O fluxo compartilha layout, estados e navegação em português do Brasil.
          </p>
        </article>
      </div>

      <StateMessage title="Catálogo em preparação">
        Os cards reais de filmes serão conectados à lista de programação nas
        próximas etapas.
      </StateMessage>
    </PageSection>
  );
}
