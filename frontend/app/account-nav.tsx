"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getSavedPortfolioToken } from "./portfolio-token";

/** "My Portfolio" / "Settings" pills — shown once a portfolio token has been
 * saved locally (i.e. the visitor has been to their portfolio/settings page
 * before). Nothing to show for a first-time, anonymous dashboard visitor. */
export function AccountNav() {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    setToken(getSavedPortfolioToken());
  }, []);

  if (!token) return null;

  return (
    <div className="mb-4 flex gap-2">
      <Link href={`/portfolio?token=${token}`} className="glass-btn px-3 py-1.5 text-xs font-medium">
        My Portfolio 💖
      </Link>
      <Link href={`/settings?token=${token}`} className="glass-btn px-3 py-1.5 text-xs font-medium">
        Settings ⚙️
      </Link>
    </div>
  );
}
