/* global React */
// CrystalOrb — canonical iridescent-glass scrying orb.
// Drop into any React project. No external deps.
//
// Variants: sapphire (default) | chrome | obsidian | amber
// Props:
//   size        px (default 80). Sizes <80 use a lighter render path.
//   variant     color family
//   active      breathing + animated interior (default true)
//   intensity   glow multiplier (default 1)
//   seed        integer — deterministic ray layout
//   onClick     if provided, renders as <button>; otherwise <span> (no nested-button warnings)
//   title       accessible name (only meaningful if onClick)
//   pool        boolean — cast an elliptical caustic pool beneath the orb
//   style       inline style overrides

const { useMemo, useId } = React;

export function CrystalOrb({
  size = 80, variant = "sapphire", active = true, intensity = 1,
  style, seed = 1, onClick, title, pool = false,
}) {
  const id = useId();
  const palette = {
    sapphire: { core: "#2947E8", mid: "#1E3CFF", rim: "#070E35", hi: "#C8D6FF", glow: "#2B4BFF", accent: "#7B5CFF" },
    chrome:   { core: "#C8CEDC", mid: "#9AA0B5", rim: "#1A1D26", hi: "#FFFFFF", glow: "#8B9CFF", accent: "#E85FCC" },
    obsidian: { core: "#1B1724", mid: "#0E0B15", rim: "#020103", hi: "#6B5A82", glow: "#7B5CFF", accent: "#4FE0D4" },
    amber:    { core: "#E8B86F", mid: "#A07A38", rim: "#2A1A08", hi: "#FFE5B8", glow: "#E8A04F", accent: "#E85FCC" },
  }[variant];

  const small = size < 80;
  const rayCount = small ? 12 : 18;

  const rays = useMemo(() => {
    const arr = [];
    let s = seed * 9301 + 49297;
    const rnd = () => { s = (s * 9301 + 49297) % 233280; return s / 233280; };
    for (let i = 0; i < rayCount; i++) {
      arr.push({
        angle: (360 / rayCount) * i + rnd() * (360 / rayCount) * 0.4,
        len: 0.55 + rnd() * 0.45,
        width: 0.4 + rnd() * 1.2,
        op: 0.25 + rnd() * 0.55,
      });
    }
    return arr;
  }, [seed, rayCount]);

  const Tag = onClick ? "button" : "span";
  const tagProps = onClick
    ? { type: "button", onClick, "aria-label": title }
    : { "aria-hidden": title ? undefined : true };

  return (
    <Tag
      {...tagProps}
      title={title}
      style={{
        width: size, height: size, padding: 0, border: "none", background: "transparent",
        cursor: onClick ? "pointer" : "default", position: "relative", display: "inline-block",
        animation: active ? `orb-breathe-${seed} 4s ease-in-out infinite` : "none",
        ...style,
      }}
    >
      {pool && (
        <div aria-hidden style={{
          position: "absolute", left: "50%", bottom: -size * 0.3,
          width: size * 1.4, height: size * 0.3, transform: "translateX(-50%)",
          background: `radial-gradient(ellipse, ${palette.glow}66, transparent 65%)`,
          filter: "blur(10px)",
          opacity: active ? 0.75 * intensity : 0.3, pointerEvents: "none",
        }} />
      )}

      <div aria-hidden style={{
        position: "absolute", inset: -size * 0.35, borderRadius: "50%",
        background: `radial-gradient(circle, ${palette.glow}66 0%, ${palette.accent}22 30%, transparent 65%)`,
        filter: `blur(${size * 0.12}px)`,
        opacity: active ? 0.95 * intensity : 0.3, pointerEvents: "none",
      }} />

      <svg viewBox="0 0 100 100" width={size} height={size}
           style={{ display: "block", overflow: "visible", position: "relative" }}>
        <defs>
          <radialGradient id={`body-${id}`} cx="38%" cy="32%" r="78%">
            <stop offset="0%" stopColor={palette.hi} />
            <stop offset="14%" stopColor={palette.core} />
            <stop offset="55%" stopColor={palette.mid} />
            <stop offset="88%" stopColor={palette.rim} />
            <stop offset="100%" stopColor="#000" />
          </radialGradient>
          <radialGradient id={`spec-${id}`} cx="28%" cy="22%" r="30%">
            <stop offset="0%" stopColor="#fff" />
            <stop offset="40%" stopColor="#fff" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#fff" stopOpacity="0" />
          </radialGradient>
          <radialGradient id={`rim-${id}`} cx="78%" cy="78%" r="45%">
            <stop offset="0%" stopColor={palette.accent} stopOpacity="0.85" />
            <stop offset="55%" stopColor={palette.glow} stopOpacity="0.3" />
            <stop offset="100%" stopColor={palette.glow} stopOpacity="0" />
          </radialGradient>
          <radialGradient id={`caustic-${id}`} cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={palette.hi} />
            <stop offset="30%" stopColor={palette.core} stopOpacity="0.7" />
            <stop offset="100%" stopColor={palette.core} stopOpacity="0" />
          </radialGradient>
          <linearGradient id={`sheen-${id}`} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%"   stopColor="#4FE0D4" stopOpacity="0" />
            <stop offset="40%"  stopColor="#7B5CFF" stopOpacity="0.35" />
            <stop offset="60%"  stopColor="#E85FCC" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#5FD0FF" stopOpacity="0" />
          </linearGradient>
          <filter id={`chroma-${id}`} x="-10%" y="-10%" width="120%" height="120%">
            <feGaussianBlur stdDeviation="0.4" />
          </filter>
          <clipPath id={`clip-${id}`}><circle cx="50" cy="50" r="46" /></clipPath>
          {!small && <filter id={`rays-blur-${id}`}><feGaussianBlur stdDeviation="0.5" /></filter>}
        </defs>

        {!small && (
          <>
            <circle cx="50.6" cy="50" r="46.5" fill="none" stroke="#FF4A7A" strokeWidth="0.35"
                    opacity="0.5" filter={`url(#chroma-${id})`} />
            <circle cx="49.4" cy="50" r="46.5" fill="none" stroke="#4FE0FF" strokeWidth="0.35"
                    opacity="0.5" filter={`url(#chroma-${id})`} />
          </>
        )}

        <circle cx="50" cy="50" r="46" fill={`url(#body-${id})`} />

        <g clipPath={`url(#clip-${id})`}>
          <g style={{
            transformOrigin: "50px 50px",
            animation: active ? `orb-spin-${seed} 45s linear infinite` : "none",
          }} opacity={active ? 1 : 0.5}>
            <g filter={small ? undefined : `url(#rays-blur-${id})`}>
              {rays.map((r, i) => (
                <line key={i}
                  x1="50" y1={50 - 42 * r.len} x2="50" y2="36"
                  stroke={palette.hi} strokeWidth={r.width} strokeLinecap="round"
                  opacity={r.op} transform={`rotate(${r.angle} 50 50)`} />
              ))}
            </g>
            <circle cx="50" cy="50" r="12" fill={`url(#caustic-${id})`} />
          </g>

          <rect x="0" y="0" width="100" height="100" fill={`url(#sheen-${id})`} style={{
            transformOrigin: "50px 50px",
            animation: active ? `orb-sheen-${seed} 9s ease-in-out infinite` : "none",
          }} />

          <circle cx="50" cy="50" r="46" fill={`url(#rim-${id})`} />
        </g>

        <ellipse cx="38" cy="28" rx="14" ry="9" fill={`url(#spec-${id})`} transform="rotate(-22 38 28)" />
        <circle cx="34" cy="24" r="1.5" fill="#fff" opacity="0.9" />
        <circle cx="50" cy="50" r="46" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="0.4" />
      </svg>

      <style>{`
        @keyframes orb-spin-${seed} { to { transform: rotate(360deg); } }
        @keyframes orb-sheen-${seed} { 0%,100% { transform: rotate(0deg); opacity: 0.5 } 50% { transform: rotate(180deg); opacity: 1 } }
        @keyframes orb-breathe-${seed} { 0%,100% { transform: scale(1); } 50% { transform: scale(1.02); } }
        @media (prefers-reduced-motion: reduce) {
          [style*="orb-spin-${seed}"],
          [style*="orb-sheen-${seed}"],
          [style*="orb-breathe-${seed}"] { animation: none !important; }
        }
      `}</style>
    </Tag>
  );
}
