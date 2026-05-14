import Link from "next/link";
import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Cinepolis Natal",
  description: "Browser frontend for the Cinepolis Natal reservation platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body>
        <div className="app-shell">
          <header className="topbar">
            <Link className="brand" href="/">
              Cinepolis Natal
            </Link>
            <nav className="nav-links" aria-label="Principal">
              <Link href="/">Home</Link>
              <Link href="/my-tickets">Meus ingressos</Link>
              <Link href="/login">Entrar</Link>
              <Link href="/register">Criar conta</Link>
            </nav>
          </header>

          <main className="page-frame">{children}</main>
        </div>
      </body>
    </html>
  );
}
