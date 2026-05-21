import type { Metadata } from "next";

import { AppHeader } from "@/components/layout/AppHeader";
import { AuthProvider } from "@/contexts/AuthContext";

import "./globals.css";

export const metadata: Metadata = {
  title: "Cinepolis Natal",
  description: "Frontend web para compra de ingressos do Cinepolis Natal.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body>
        <AuthProvider>
          <div className="app-shell">
            <a className="skip-link" href="#conteudo">
              Pular para o conteúdo
            </a>
            <AppHeader />
            <main className="main-content" id="conteudo" tabIndex={-1}>
              <div className="shell-container">{children}</div>
            </main>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
