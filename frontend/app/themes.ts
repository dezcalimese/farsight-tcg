export type ThemeId = "xatu" | "pikachu" | "clefairy" | "azumarill";

export const THEMES: { id: ThemeId; label: string; motif: string }[] = [
  { id: "xatu", label: "Xatu", motif: "eye" },
  { id: "pikachu", label: "Pikachu", motif: "bolt" },
  { id: "clefairy", label: "Clefairy", motif: "star" },
  { id: "azumarill", label: "Azumarill", motif: "drop" },
];

export const DEFAULT_THEME: ThemeId = "xatu";
