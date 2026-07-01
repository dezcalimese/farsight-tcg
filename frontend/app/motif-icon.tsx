// Small original pixel-style motif icons (hand-drawn geometry, not character
// artwork) used per theme instead of reproducing trademarked Pokemon sprites.

export function MotifIcon({ motif, className }: { motif: string; className?: string }) {
  const common = { className, shapeRendering: "crispEdges" as const, viewBox: "0 0 16 16" };

  switch (motif) {
    case "bolt":
      return (
        <svg {...common}>
          <path d="M9 1 4 9h3l-1 6 6-9H9l1-5z" fill="currentColor" />
        </svg>
      );
    case "star":
      return (
        <svg {...common}>
          <path
            d="M8 1l1.6 4.6H14l-3.8 2.8L11.6 13 8 10.2 4.4 13l1.4-4.6L2 5.6h4.4z"
            fill="currentColor"
          />
        </svg>
      );
    case "drop":
      return (
        <svg {...common}>
          <path d="M8 1c3 4 5 6.5 5 9a5 5 0 0 1-10 0c0-2.5 2-5 5-9z" fill="currentColor" />
        </svg>
      );
    case "eye":
    default:
      return (
        <svg {...common}>
          <path
            d="M1 8s3-5 7-5 7 5 7 5-3 5-7 5-7-5-7-5z"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          />
          <circle cx="8" cy="8" r="2.5" fill="currentColor" />
        </svg>
      );
  }
}

export function PokeballPlaceholder({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 16 16" className={className} shapeRendering="crispEdges">
      <circle cx="8" cy="8" r="7" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <path d="M1 8h14" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="8" cy="8" r="2.2" fill="currentColor" />
    </svg>
  );
}
