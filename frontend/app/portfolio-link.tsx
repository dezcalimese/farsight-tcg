"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getSavedPortfolioToken } from "./portfolio-token";

export function PortfolioLink() {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    setToken(getSavedPortfolioToken());
  }, []);

  if (!token) return null;

  return (
    <Link
      href={`/portfolio?token=${token}`}
      className="glass-btn whitespace-nowrap px-3 py-1.5 text-xs font-medium"
    >
      My Portfolio 💖
    </Link>
  );
}
