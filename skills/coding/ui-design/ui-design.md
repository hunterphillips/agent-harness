# UI Design

Searchable database of UI/UX design rules with priority-based recommendations: 84 styles, 192 color palettes, 74 font pairings, 192 product types with reasoning rules, 98 UX guidelines, 104 icon entries, 16 GSAP motion presets, and 25 chart types across 22 technology stacks. Ported from [ui-ux-pro-max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) (MIT).

## When to apply

Use for **UI structure, visual design decisions, interaction patterns, or user experience quality control**: designing new pages, creating/refactoring UI components, choosing color/typography/spacing/layout systems, reviewing UI for UX/accessibility/consistency, implementing navigation/animation/responsive behavior.

Skip it for pure backend logic, API/database design, non-visual performance work, or infrastructure — unless the task changes how something **looks, feels, moves, or is interacted with**.

## Running the search tool

Scripts live inside this workflow's folder. Resolve the path from the coding skill's base directory (announced when the skill loaded); in deployed projects that is:

```bash
python3 .claude/skills/coding/ui-design/scripts/search.py "<query>" --domain <domain>
```

All commands below abbreviate this as `search.py`. Requires Python 3.x, no external dependencies.

## Rule categories by priority

_Follow priority 1→10 to decide which category to focus on first; use `--domain <domain>` to query full details. Full rule text lives in [references/quick-reference.md](references/quick-reference.md) — read it on demand rather than loading it every time._

| Priority | Category | Impact | Domain | Key checks (must have) | Anti-patterns (avoid) |
|----------|----------|--------|--------|------------------------|------------------------|
| 1 | Accessibility | CRITICAL | `ux` | Contrast 4.5:1, alt text, keyboard nav, aria-labels | Removing focus rings, icon-only buttons without labels |
| 2 | Touch & interaction | CRITICAL | `ux` | Min size 44×44px, 8px+ spacing, loading feedback | Reliance on hover only, instant state changes (0ms) |
| 3 | Performance | HIGH | `ux` | WebP/AVIF, lazy loading, reserve space (CLS < 0.1) | Layout thrashing, cumulative layout shift |
| 4 | Style selection | HIGH | `style`, `product` | Match product type, consistency, SVG icons (no emoji) | Mixing flat & skeuomorphic randomly, emoji as icons |
| 5 | Layout & responsive | HIGH | `ux` | Mobile-first breakpoints, viewport meta, no horizontal scroll | Horizontal scroll, fixed px container widths, disable zoom |
| 6 | Typography & color | MEDIUM | `typography`, `color` | Base 16px, line-height 1.5, semantic color tokens | Text < 12px body, gray-on-gray, raw hex in components |
| 7 | Animation | MEDIUM | `ux`, `gsap` | Duration 150–300ms, motion conveys meaning, spatial continuity | Decorative-only animation, animating width/height, no reduced-motion |
| 8 | Forms & feedback | MEDIUM | `ux` | Visible labels, error near field, helper text, progressive disclosure | Placeholder-only label, errors only at top, overwhelm upfront |
| 9 | Navigation patterns | HIGH | `ux` | Predictable back, bottom nav ≤5, deep linking | Overloaded nav, broken back behavior, no deep links |
| 10 | Charts & data | LOW | `chart` | Legends, tooltips, accessible colors | Relying on color alone to convey meaning |

For app-specific polish rules (icons, touch feedback, dark mode contrast, safe areas) and the canonical pre-delivery checklist, read [references/pro-rules.md](references/pro-rules.md).

## Workflow

### Step 1: Analyze requirements

Extract from the user request:

- **Product type**: SaaS, e-commerce, portfolio, dashboard, entertainment, tool, productivity, or hybrid
- **Target audience & context**: age group, usage context (commute, leisure, work)
- **Style keywords**: playful, vibrant, minimal, dark mode, content-first, immersive, etc.
- **Stack**: detect from the project — check `package.json` deps (react/next/vue/svelte/nuxt/@angular), `pubspec.yaml` (Flutter), `*.xcodeproj`/`Package.swift` (SwiftUI), `composer.json` (Laravel), or React Native markers (`app.json` + `react-native` dep). If nothing is detectable, ask the user or default to `html-tailwind`. **Never assume a stack** — a hardcoded default silently misroutes every recommendation.

### Step 2: Generate design system (REQUIRED for new pages/projects)

Always start with `--design-system` to get comprehensive recommendations with reasoning:

```bash
search.py "<product_type> <industry> <keywords>" --design-system [-p "Project Name"]
```

This searches product/style/color/landing/typography domains in parallel, applies reasoning rules from `ui-reasoning.csv`, and returns pattern, style, colors, typography, effects, and anti-patterns to avoid.

**Example:**

```bash
search.py "beauty spa wellness service" --design-system -p "Serenity Spa"
```

### Step 2b: Persist design system (master + overrides pattern)

To save the design system for retrieval across sessions, add `--persist` **and always pass `--output-dir` pointed at the project root** — without it, files are written relative to whatever directory the tool happens to run from:

```bash
search.py "<query>" --design-system --persist -p "Project Name" --output-dir "<project-root>"
```

This creates:

- `design-system/<project-slug>/MASTER.md` — global source of truth
- `design-system/<project-slug>/pages/` — folder for page-specific overrides

With a page-specific override, add `--page "dashboard"` to also create `design-system/<project-slug>/pages/dashboard.md`.

If `MASTER.md` already exists, `--persist` **skips writing and leaves it untouched** unless you also pass `--force` — check whether it exists (and read it) before regenerating, so you don't silently discard prior decisions.

**Retrieval when building a specific page:**

1. Read `design-system/<project-slug>/MASTER.md`
2. If `design-system/<project-slug>/pages/<page-name>.md` exists, its rules override master
3. Otherwise use master rules exclusively

### Step 2c: Design dials (optional)

Three optional 1-10 sliders that tune `--design-system` output without changing the query:

```bash
search.py "<query>" --design-system --variance <1-10> --motion <1-10> --density <1-10>
```

| Dial | Low (1-3) | Mid (4-7) | High (8-10) |
|------|-----------|-----------|-------------|
| `--variance` | Centered / minimal | Balanced / modern | Bold / asymmetric (Brutalism, Bento Grids) |
| `--motion` | Subtle micro-interactions | Standard scroll/stagger motion | Complex choreography (pin, Flip, SplitText) |
| `--density` | Spacious (24-96px spacing scale) | Standard (16-64px, default) | Dense/dashboard (8-32px spacing scale) |

- `--motion` attaches a ready-to-use GSAP snippet (framework notes, Do/Don't, performance notes) matched to the resolved tier.
- `--density` overrides the `--space-*` CSS variable table in the output — dashboards (high) vs. marketing pages (low) without hand-editing tokens.
- Leaving a dial unset keeps that part of the output unchanged.

### Step 3: Supplement with detailed searches (as needed)

```bash
search.py "<keyword>" --domain <domain> [-n <max_results>]
```

| Need | Domain | Example |
|------|--------|---------|
| Product type patterns | `product` | `--domain product "entertainment social"` |
| More style options | `style` | `--domain style "glassmorphism dark"` |
| Color palettes | `color` | `--domain color "entertainment vibrant"` |
| Font pairings | `typography` | `--domain typography "playful modern"` |
| Individual Google Fonts | `google-fonts` | `--domain google-fonts "sans serif popular variable"` |
| Chart recommendations | `chart` | `--domain chart "real-time dashboard"` |
| UX best practices | `ux` | `--domain ux "animation accessibility"` |
| Landing page structure | `landing` | `--domain landing "hero social-proof"` |
| Icon recommendations | `icons` | `--domain icons "navigation outline"` |
| GSAP animation presets | `gsap` | `--domain gsap "scroll reveal stagger"` |
| React/Next.js performance | `react` | `--domain react "rerender memo list"` |
| App/native interface guidelines | `web` | `--domain web "accessibilityLabel touch safe-areas"` |

Domain is auto-detected from the query if `--domain` is omitted — but auto-detection can misroute overlapping terms (e.g. "font" matches both `typography` and `google-fonts`). If results look off-topic, pass `--domain` explicitly.

### Step 4: Stack guidelines

```bash
search.py "<keyword>" --stack <stack>
```

**Available stacks:** `react`, `nextjs`, `vue`, `svelte`, `astro`, `nuxtjs`, `nuxt-ui`, `angular`, `laravel`, `swiftui`, `react-native`, `flutter`, `jetpack-compose`, `html-tailwind`, `shadcn`, `threejs`, `javafx`, `wpf`, `winui`, `avalonia`, `uno`, `uwp`. Use the stack detected in Step 1.

## If a search returns 0 results

Do not fabricate output. Instead:

1. Retry once with broader or differently-worded keywords (try product + style separately rather than combined).
2. If still empty, fall back to the priority table above and say explicitly that the recommendation came from the built-in defaults, not a database match.
3. Never present a 0-result search as if it returned data.

## Example workflow

**User request:** "Make an AI search homepage." (stack detected as Next.js from `package.json`)

```bash
# Step 2: design system
search.py "AI search tool modern minimal" --design-system -p "AI Search"

# Step 3: supplement
search.py "search loading animation" --domain ux

# Step 4: stack guidelines
search.py "suspense streaming bundle" --stack nextjs
```

Then synthesize the design system + detailed searches and implement.

## Output formats

`--design-system` supports `-f ascii` (default, terminal display), `-f markdown` (documentation), and `--json` (machine-readable, includes the raw design system dict plus persistence status).

## Tips for better results

- Use **multi-dimensional keywords** — combine product + industry + tone + density: `"entertainment social vibrant content-dense"`, not just `"app"`
- Try different phrasings for the same need: `"playful neon"` → `"vibrant dark"` → `"content-first minimal"`
- Use `--design-system` first for full recommendations, then `--domain` to deep-dive any dimension
- Pass the detected stack explicitly for implementation-specific guidance

| Problem | What to do |
|---------|------------|
| Can't decide on style/color | Re-run `--design-system` with different keywords |
| Dark mode contrast issues | [references/quick-reference.md](references/quick-reference.md) §6: `color-dark-mode` + `color-accessible-pairs` |
| Animations feel unnatural | §7: `spring-physics` + `easing` + `exit-faster-than-enter` |
| Form UX is poor | §8: `inline-validation` + `error-clarity` + `focus-management` |
| Navigation feels confusing | §9: `nav-hierarchy` + `bottom-nav-limit` + `back-behavior` |
| Layout breaks on small screens | §5: `mobile-first` + `breakpoint-consistency` |
| Performance / jank | §3: `virtualize-lists` + `main-thread-budget` + `debounce-throttle` |

## Before delivering app UI

For native/mobile app UI (iOS/Android/React Native/Flutter), read [references/pro-rules.md](references/pro-rules.md) and run through its pre-delivery checklist: icon/visual-element discipline, interaction feedback, light/dark contrast, safe-area layout, accessibility.
