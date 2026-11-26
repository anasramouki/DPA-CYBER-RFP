import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'DPA-CYBER-RFP — Veille Marchés Publics & Cybersécurité',
  description:
    'Plateforme DPA-CYBER-RFP de veille stratégique en temps réel des appels d\'offres cybersécurité et marchés publics au Maroc.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
        <link rel="icon" href="/favicon.ico" sizes="any" />
      </head>
      <body>{children}</body>
    </html>
  );
}
