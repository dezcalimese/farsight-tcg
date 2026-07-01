import { Baloo_2, JetBrains_Mono, Nunito } from "next/font/google";

export const heading = Baloo_2({
  weight: ["600", "700", "800"],
  subsets: ["latin"],
  variable: "--font-heading",
});

export const body = Nunito({
  subsets: ["latin"],
  variable: "--font-body",
});

export const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});
