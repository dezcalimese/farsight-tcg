import { JetBrains_Mono, Space_Grotesk } from "next/font/google";

export const heading = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-heading",
});

export const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});
