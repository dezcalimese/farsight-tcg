import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Farsight — Pokemon TCG Intelligence Feed",
  description: "Trending cards, restocks, and news for the Pokemon TCG market.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-bg text-white antialiased">{children}</body>
    </html>
  );
}
