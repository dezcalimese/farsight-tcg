import type { Metadata } from "next";
import { body, heading, mono } from "./fonts";
import "./globals.css";
import { ThemeProvider } from "./theme-provider";

export const metadata: Metadata = {
  title: "Farsight — Pokemon TCG Intelligence Feed",
  description: "Trending cards, restocks, and news for the Pokemon TCG market.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="xatu">
      <body
        className={`${heading.variable} ${body.variable} ${mono.variable} font-body min-h-screen antialiased`}
      >
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
