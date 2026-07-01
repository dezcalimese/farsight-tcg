"use client";

import { MotifIcon } from "./motif-icon";
import { useTheme } from "./theme-provider";
import { THEMES } from "./themes";

export function ThemeSwitcher() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="flex gap-1.5">
      {THEMES.map((t) => (
        <button
          key={t.id}
          type="button"
          aria-label={`${t.label} theme`}
          title={t.label}
          onClick={() => setTheme(t.id)}
          data-active={theme === t.id}
          className="glass-btn flex h-9 w-9 items-center justify-center"
        >
          <MotifIcon motif={t.motif} className="h-4 w-4" />
        </button>
      ))}
    </div>
  );
}
