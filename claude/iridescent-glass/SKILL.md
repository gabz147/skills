---
name: iridescent-glass
description: Build UI in the "scrying instrument" aesthetic — deep obsidian glass, iridescent chromatic-aberration rims (teal→violet→magenta→cyan), crystal orbs with caustic pools, liquid-metal backgrounds, serif-italic focal words, pill-shaped CTAs with iridescent stroke. Use when the user asks for "Mercura style", "iridescent", "holographic", "liquid metal", "chromatic rim", "crystal orb UI", "scrying UI", or references images of glossy dark-glass + rainbow-rim components. Skip for flat/brutalist/minimal/paper/neubrutalist styles.
---

# Iridescent Glass — scrying-instrument UI

A concentrated dark aesthetic built on four motifs: **obsidian glass bodies**, **chromatic-aberration iridescent rims**, **caustic-pool reflections**, and **liquid-metal atmospheric backgrounds**. Serif display type (italic for focal words), mono numerals, uppercase labels, asymmetric hero layouts.

## Trigger signals

Apply this skill when the user mentions: *iridescent, holographic, oil slick, liquid metal, chromatic aberration, scrying, crystal orb, Mercura, glossy black glass, rainbow rim, obsidian UI, dichroic*. Also when they reference images that look like polished dark pill buttons ringed in refracted light, blue/violet crystal spheres, or oil-slick fluid backgrounds.

Do **not** apply for: flat design, neubrutalism, paper/sketchy, pastel, skeuomorphic woodgrain, Material 3, corporate dashboards.

---

## Core palette (CSS variables)

Drop this into the root stylesheet. These are the exact canonical values — don't drift.

```css
:root {
  /* Backgrounds (dark only — this aesthetic is dark-mode-native) */
  --bg-0: #000000; --bg-1: #07080B; --bg-2: #0C0E14; --bg-3: #14161F;

  /* Accent: sapphire is the primary action hue */
  --sapphire-core: #1E3CFF; --sapphire-rim: #0A1A55; --sapphire-glow: #3A5BFF;

  /* The iridescent quartet — always in this order on the spectrum */
  --iri-teal: #4FE0D4; --iri-violet: #7B5CFF; --iri-magenta: #E85FCC; --iri-cyan: #5FD0FF;

  /* Text: warm-neutral ink, never pure white */
  --ink: #E8E4D8; --ink-dim: #A8A397;

  /* Secondary accent: antique gold for labels and small-caps headers */
  --gold: #B89968; --gold-dim: #8A7349;

  /* Semantic */
  --ok: #4FE0A8; --warn: #E8B86F; --danger: #E85F7B;

  /* Glass surface */
  --glass: rgba(255, 255, 255, 0.04);
  --glass-hi: rgba(255, 255, 255, 0.07);
  --stroke: rgba(232, 228, 216, 0.08);
  --stroke-hi: rgba(232, 228, 216, 0.16);

  /* Type */
  --font-serif: 'Cormorant Garamond', 'EB Garamond', serif;
  --font-sans:  'Inter', ui-sans-serif, system-ui, sans-serif;
  --font-mono:  'JetBrains Mono', ui-monospace, monospace;

  /* Motion */
  --iri-speed: 8s;   /* rotation period of iridescent rim */
  --grain: 0.08;     /* atmospheric noise opacity */
}

@property --iri-angle { syntax: '<angle>'; inherits: false; initial-value: 0deg; }
@property --sheen-x   { syntax: '<percentage>'; inherits: false; initial-value: -40%; }
```

**Rules:**
- Background is always near-black. Never use `#fff` as a body background.
- Text is `var(--ink)` (warm off-white), never `#fff`. This is non-negotiable.
- Labels and small UI meta are uppercase, 11px, `letter-spacing: 0.18em`, `color: var(--gold)`.
- Numerals use `font-feature-settings: "tnum"` for tabular alignment.
- The iridescent spectrum is *always* teal → violet → magenta → cyan → teal. Never shuffle.

---

## The four core primitives

### 1. Iridescent surface (`.iridescent`)

The base shimmer. Use on active primary buttons, active tabs, progress fills.

```css
.iridescent {
  position: relative; overflow: hidden; isolation: isolate;
  background: conic-gradient(from var(--iri-angle, 0deg) at 50% 50%,
    #4FE0D4 0deg, #7B5CFF 90deg, #E85FCC 180deg, #5FD0FF 270deg, #4FE0D4 360deg);
  animation: iri-angle-spin var(--iri-speed) linear infinite;
  filter: saturate(0.95) brightness(0.98);
}
.iridescent::before {
  content: ""; position: absolute; inset: -20%;
  background: linear-gradient(110deg, transparent 38%, rgba(255,255,255,0.3) 50%, transparent 62%);
  transform: translateX(var(--sheen-x));
  animation: sheen 6s cubic-bezier(.4,0,.6,1) infinite;
  mix-blend-mode: screen; pointer-events: none;
}
@keyframes iri-angle-spin { to { --iri-angle: 360deg; } }
@keyframes sheen { 0%,100% { --sheen-x: -60%; } 50% { --sheen-x: 160%; } }
```

### 2. Iridescent 1px stroke (`.iri-stroke`)

The chromatic rim on pill buttons, cards, focus rings. This is the **signature look**.

```css
.iri-stroke { position: relative; }
.iri-stroke::before {
  content: ""; position: absolute; inset: 0; border-radius: inherit; padding: 1px;
  background: conic-gradient(from var(--iri-angle, 0deg),
    #4FE0D4, #7B5CFF, #E85FCC, #5FD0FF, #4FE0D4);
  animation: iri-angle-spin var(--iri-speed) linear infinite;
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor; mask-composite: exclude;
  pointer-events: none; opacity: 0.7;
}
```

Apply to any rounded element. The mask-composite trick keeps the gradient as a border only.

### 3. Glass card (`.glass`)

```css
.glass {
  background: var(--glass);
  backdrop-filter: blur(14px) saturate(1.1);
  -webkit-backdrop-filter: blur(14px) saturate(1.1);
  border: 1px solid var(--stroke); border-radius: 14px;
}
.glass:hover { border-color: var(--stroke-hi); }
```

Pair with `.iri-stroke` for the chromatic rim treatment.

### 4. Atmosphere background (`.mercura-bg` + drift blobs)

Every full-screen view sits on this.

```css
.mercura-bg {
  position: relative;
  background:
    radial-gradient(ellipse 80% 60% at 50% 40%, #0E1020 0%, #07080B 45%, #000 100%),
    #000;
}
.mercura-bg::after {
  /* persistent grain */
  content: ""; position: absolute; inset: 0; pointer-events: none; z-index: 0;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 1  0 0 0 0 0.95  0 0 0 0 0.85  0 0 0 0.6 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
  opacity: var(--grain); mix-blend-mode: overlay;
}
.mercura-bg::before {
  /* vignette + mouse spotlight */
  content: ""; position: absolute; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(circle at var(--mouse-x, 50%) var(--mouse-y, 50%), rgba(255,255,255,0.05), transparent 30%),
    radial-gradient(ellipse at 0% 0%,   rgba(0,0,0,0.55), transparent 50%),
    radial-gradient(ellipse at 100% 0%, rgba(0,0,0,0.55), transparent 50%),
    radial-gradient(ellipse at 0% 100%, rgba(0,0,0,0.70), transparent 50%),
    radial-gradient(ellipse at 100% 100%, rgba(0,0,0,0.70), transparent 50%);
}

.drift-blobs { position: absolute; inset: 0; pointer-events: none; overflow: hidden; z-index: 0; }
.drift-blobs > span {
  position: absolute; border-radius: 50%; filter: blur(120px); opacity: 0.15;
  animation: drift 40s ease-in-out infinite;
}
.drift-blobs .b1 { width: 520px; height: 520px; background: #1E3CFF; left: -10%; top: 10%; }
.drift-blobs .b2 { width: 420px; height: 420px; background: #7B5CFF; right: -8%; top: 40%; animation-delay: -10s; }
.drift-blobs .b3 { width: 360px; height: 360px; background: #4FE0D4; left: 30%; bottom: -10%; animation-delay: -20s; }
.drift-blobs .b4 { width: 300px; height: 300px; background: #E85FCC; right: 25%; top: -5%; animation-delay: -30s; opacity: 0.08; }
@keyframes drift {
  0%,100% { transform: translate(0,0) scale(1); }
  33%     { transform: translate(40px,-30px) scale(1.05); }
  66%     { transform: translate(-30px,40px) scale(0.95); }
}
```

Attach a `pointermove` listener on the container and set `--mouse-x` / `--mouse-y` on the element for the spotlight.

---

## Crystal Orb — the centerpiece

The orb is an SVG, **not** a CSS-only element. It has: body radial gradient, specular gloss, rim light, starburst rays (seeded), caustic pool beneath. Four variants: `sapphire` (default), `chrome`, `obsidian`, `amber`.

**Implementation philosophy:**
- `<svg viewBox="0 0 100 100">` at any size.
- `radialGradient` for body: hi (14%) → core (14%) → mid (55%) → rim (88%) → #000.
- `radialGradient` for specular at cx=28% cy=22% r=30%.
- Seeded deterministic rays (12 for small, 18 for large) rendered as lines from center.
- Optional "pool" prop: an elliptical blurred shadow below, same hue as glow.
- Breathing animation when `active`: `transform: scale(1) → scale(1.02) → scale(1)` over 4s.

**Key rule:** a decorative orb must NOT be a `<button>`. Render as `<span>` unless it has `onClick`. Nested `<button>` inside `<button>` violates HTML and triggers React warnings.

**Palette per variant:**
- `sapphire`: core `#2947E8`, mid `#1E3CFF`, rim `#070E35`, hi `#C8D6FF`, glow `#2B4BFF`, accent `#7B5CFF`
- `chrome`: core `#C8CEDC`, mid `#9AA0B5`, rim `#1A1D26`, hi `#FFFFFF`, glow `#8B9CFF`, accent `#E85FCC`
- `obsidian`: core `#1B1724`, mid `#0E0B15`, rim `#020103`, hi `#6B5A82`, glow `#7B5CFF`, accent `#4FE0D4`
- `amber`: core `#E8B86F`, mid `#A07A38`, rim `#2A1A08`, hi `#FFE5B8`, glow `#E8A04F`, accent `#E85FCC`

See `references/crystal-orb.jsx` in this skill directory for the canonical React implementation.

---

## Liquid button (primary CTA)

Pill-shaped, iridescent-filled for primary, glass for secondary.

```jsx
<button
  className="iri-focus press"
  style={{
    position: "relative", display: "inline-flex", alignItems: "center", gap: 8,
    padding: "12px 22px", fontSize: 14, fontWeight: 500, letterSpacing: "0.02em",
    border: "1px solid transparent", borderRadius: 999,
    color: "#0A0A0F",  /* dark text on iridescent fill */
    overflow: "hidden", isolation: "isolate",
    transition: "transform 180ms cubic-bezier(.22,1,.36,1)",
  }}
>
  <span aria-hidden className="iridescent" style={{ position: "absolute", inset: 0, zIndex: -1 }} />
  <span style={{ position: "relative", zIndex: 1 }}>Continue →</span>
</button>
```

Secondary variant: swap the `iridescent` span for `background: rgba(255,255,255,0.05); borderColor: var(--stroke-hi); color: var(--ink);`.
Ghost variant: `background: transparent; color: var(--ink-dim);`.

On `mouseDown`, capture press coordinates and animate an expanding white circle from that point (`iri-pool` keyframe, 500ms). This is the "ink pool" affordance.

---

## Typography grammar

Headlines use serif with an italic focal word in gold:

```jsx
<h1 className="serif" style={{
  fontSize: "clamp(52px, 6.5vw, 92px)", margin: 0, fontWeight: 500,
  letterSpacing: "-0.025em", lineHeight: 0.95, color: "var(--ink)",
}}>
  Study like<br/>
  you're <em style={{ fontStyle: "italic", fontWeight: 500, color: "var(--gold)" }}>scrying</em>.
</h1>
```

Supporting classes:
```css
.serif     { font-family: var(--font-serif); font-weight: 500; letter-spacing: -0.015em; }
.smallcaps { font-family: var(--font-serif); font-variant: small-caps; letter-spacing: 0.1em; }
.label     { font-family: var(--font-sans); text-transform: uppercase; letter-spacing: 0.18em;
             font-size: 11px; color: var(--gold); font-weight: 500; }
.num       { font-variant-numeric: tabular-nums; font-feature-settings: "tnum"; }
```

Wordmarks use small-caps serif: `font-variant: small-caps; letter-spacing: 0.22em;`.

---

## Layout grammar — break symmetry

Hero sections use **asymmetric grids** with a vertical hairline rule between columns:

```css
grid-template-columns: minmax(320px, 1fr) 1px minmax(420px, 1fr);
```

The orb sits in the left column, offset with `transform: translateX(-8%)` — **never centered**. The middle column is a 1px vertical gradient:

```css
background: linear-gradient(180deg, transparent, rgba(232,228,216,0.15), transparent);
```

Heading fits against the right side of the rule. This asymmetry is what separates this style from generic dark glassmorphism.

---

## Motion rules

- **Iridescent rotation**: 8s default. Slow down to 14s on ambient surfaces, speed to 3s on hover.
- **Easing**: prefer `cubic-bezier(.22,1,.36,1)` (emphatic decelerate) for most transitions. Use `cubic-bezier(.4,0,.6,1)` for sheen sweeps.
- **Sheen sweep**: 6s period, runs across iridescent fills perpetually.
- **Orb breathing**: 4s period, 2% scale delta, only when `active`.
- **Entry animation**: `fadeUp` — translateY(12px) → 0 over 700ms with the emphatic ease. Nested content staggers at 500ms.
- **Press feedback**: scale(0.98) on `:active`, plus the ink-pool ripple from press origin.
- **Floating orbs in constellation views**: 8–12s ease-in-out, -6 to -12px vertical drift, phase-staggered.

**Respect `prefers-reduced-motion`:**
```css
@media (prefers-reduced-motion: reduce) {
  .iridescent, .iri-stroke::before, .iridescent-soft,
  .iridescent::before, .drift-blobs > span { animation: none !important; }
}
```

---

## Focus, underlines, chips

```css
.iri-focus:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px #000, 0 0 0 4px var(--iri-violet);
}
.iri-underline { position: relative; display: inline-block; }
.iri-underline::after {
  content: ""; position: absolute; left: 0; bottom: -3px; height: 1px; width: 100%;
  background: linear-gradient(90deg, #4FE0D4, #7B5CFF, #E85FCC, #5FD0FF);
  transform: scaleX(0); transform-origin: left;
  transition: transform 300ms cubic-bezier(.22,1,.36,1);
}
.iri-underline:hover::after { transform: scaleX(1); }
```

Chips are pill-shaped, uppercase, 0.1em tracking. Tones: `neutral`, `gold`, `sapphire`, `danger` — each with matching bg/border/fg at matching alpha tiers.

---

## Decision tree — when to use what

| Need | Use |
|---|---|
| Primary CTA | Pill `<button>` with `.iridescent` fill and dark text |
| Secondary CTA | Pill `<button>` with `.glass` + `.iri-stroke` |
| Active tab / selected state | `.iridescent` fill with `zIndex: -1` behind text |
| Card / panel | `.glass` (+ `.iri-stroke` for emphasis) |
| Brand/hero element | `CrystalOrb` SVG, size 120–320, with `pool` prop |
| Small avatar/provider mark | `CrystalOrb` size 28–64, no pool |
| Section label | `.label` (uppercase gold, 0.18em) |
| Headline focal word | `<em>` in serif italic, `color: var(--gold)` |
| Background layer | `.mercura-bg` + `<div className="drift-blobs">` |
| Progress/retention visuals | SVG paths stroked with `linearGradient` using iri quartet |
| Heatmap intensity | Alpha-ramp on `rgba(30,60,255, α)` with sapphire glow past 0.5 |

---

## Performance and accessibility

- `backdrop-filter` is expensive on Safari — cap glass layers per viewport to ~6.
- `feTurbulence` for grain is GPU-friendly when static. Never animate the filter; animate a translated copy instead.
- The conic-gradient + `@property --iri-angle` animation is hardware-accelerated. Fine to run site-wide.
- Don't stack more than 3 drift blobs with `blur(120px)` — compositing cost is real.
- Dark-only by default. If forced to offer a light mode: swap `--bg-*` to pale tints, keep the iridescent quartet but drop to 0.4 opacity, make text darker (`#1A1A1A`). This aesthetic is native to dark; light is a fallback.
- Contrast: `var(--ink)` on `var(--bg-1)` = 14.2:1. `var(--gold)` on `var(--bg-1)` = 7.1:1. All AA.
- `prefers-reduced-motion`: disable conic spin, sheen, drift blobs, orb breathing. Keep static gradients.

---

## Anti-patterns (do NOT do this)

- **Don't** use `#fff` text — always `var(--ink)`.
- **Don't** use the iri quartet as *fills* for large surfaces — only as rims, accents, or animated gradients. A full-page iridescent fill is garish.
- **Don't** center everything. This style lives by asymmetry: offset the hero orb, right-align against the vertical rule.
- **Don't** use emoji icons. Icons are 1.5-stroke line SVGs (Feather-style), 16×16, `currentColor`.
- **Don't** use rounded-rect buttons. CTAs are full pills (`border-radius: 999px`). Cards are 14–22px radius.
- **Don't** mix fonts outside the trio (Cormorant Garamond / Inter / JetBrains Mono). No Roboto, no system-only.
- **Don't** nest a `<button>` inside another `<button>`. Use `<span>` for decorative orbs.

---

## References

- `references/crystal-orb.jsx` — canonical orb component
- `references/tokens.css` — canonical token file (copy into any new project)
- Mercura project at `C:\Users\Tarlu\Desktop\Mercura\Mercura\` is the living reference implementation

Related techniques worth studying: [Paper Design shaders](https://shaders.paper.design/liquid-metal) (WebGL liquid metal via `@paper-design/shaders-react`), [liquid-glass-react](https://github.com/rdev/liquid-glass-react) (Apple-style refraction via displacement maps + backdrop-filter), Robb Owen's [CSS blend-mode shaders](https://robbowen.digital/wrote-about/css-blend-mode-shaders/) (color-dodge + multiply layering), [electrikmilk/liquid-css](https://github.com/electrikmilk/liquid-css) (refractive chromatic aberration). These are complementary — reach for the WebGL shader when you need true fluid motion; CSS conic + mask-composite is enough for rims and accents.
