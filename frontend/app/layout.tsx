import type { Metadata } from "next";
import { heading, mono } from "./fonts";
import "./globals.css";
import { ThemeProvider } from "./theme-provider";

export const metadata: Metadata = {
  title: "Farsight — Pokemon TCG Intelligence Feed",
  description: "Trending cards, restocks, and news for the Pokemon TCG market.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="xatu">
      <body className={`${heading.variable} ${mono.variable} min-h-screen font-sans antialiased`}>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
