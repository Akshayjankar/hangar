import type { Metadata } from "next";
import "../styles/globals.css";

export const metadata: Metadata = {
  title: "Hangar",
  description: "A personal control panel for your localhost projects.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
