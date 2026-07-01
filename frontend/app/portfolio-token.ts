const STORAGE_KEY = "farsight-portfolio-token";

export function savePortfolioToken(token: string) {
  window.localStorage.setItem(STORAGE_KEY, token);
}

export function getSavedPortfolioToken(): string | null {
  return window.localStorage.getItem(STORAGE_KEY);
}
