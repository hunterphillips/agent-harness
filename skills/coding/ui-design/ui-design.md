# UI Design

Design UI that fits its product and its audience, then build it to the platform's floors. A searchable database backs the work: 84 styles, 192 color palettes, 74 font pairings, 192 product types with reasoning rules, 98 UX guidelines, 104 icon entries, 16 GSAP motion presets, and 25 chart types across 22 technology stacks. Ported from [ui-ux-pro-max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) (MIT). The database is a source of candidates and checks; the design direction is yours.

## When to apply

Use for **UI structure, visual design decisions, interaction patterns, or user experience quality control**: designing new pages, creating/refactoring UI components, choosing color/typography/spacing/layout systems, reviewing UI for UX/accessibility/consistency, implementing navigation/animation/responsive behavior.

Skip it for pure backend logic, API/database design, non-visual performance work, or infrastructure — unless the task changes how something **looks, feels, moves, or is interacted with**.

## Running the search tool

Scripts live inside this workflow's folder. Resolve the path from the coding skill's base directory (announced when the skill loaded):

```bash
python3 <coding-skill-dir>/ui-design/scripts/search.py "<query>" --domain <domain>
```

All commands below abbreviate this as `search.py`. Requires Python 3.x, no external dependencies.

## Floors and defaults

Two kinds of rule live in the references, and they carry different weight.

**Floors** hold for any design, whatever its style: contrast 4.5:1 (3:1 for large text), visible focus states, labels on icon-only controls, keyboard navigation, touch targets of 44×44pt / 48×48dp with 8px between them, no horizontal page scroll, zoom never disabled, `prefers-reduced-motion` respected, no information carried by color alone, loading feedback on async actions, errors next to the field. A design that breaks one is wrong, not edgy.

**Defaults** are what works when nothing argues otherwise: 150–300 ms micro-interactions, ease-out in and ease-in out, a few animated elements per view, base 16px type, line-height 1.5, semantic color tokens, bottom navigation of five or fewer. Depart from a default when the direction calls for it and you can say why; a motion-heavy landing page that stages its hero over two seconds is a choice, not a violation.

The full rule text is in [references/quick-reference.md](references/quick-reference.md), by category (accessibility, touch, performance, style, layout, typography and color, animation, forms, navigation, charts); read a category on demand rather than loading the file every time. App-specific polish (icons, touch feedback, dark-mode contrast, safe areas) and the pre-delivery checklist are in [references/pro-rules.md](references/pro-rules.md).

## Workflow

### Step 1: Analyze requirements

Extract from the user request:

- **Product type**: SaaS, e-commerce, portfolio, dashboard, entertainment, tool, productivity, or hybrid
- **Target audience & context**: age group, usage context (commute, leisure, work)
- **Style keywords**: playful, vibrant, minimal, dark mode, content-first, immersive, etc.
- **Stack**: detect from the project — check `package.json` deps (react/next/vue/svelte/nuxt/@angular), `pubspec.yaml` (Flutter), `*.xcodeproj`/`Package.swift` (SwiftUI), `composer.json` (Laravel), or React Native markers (`app.json` + `react-native` dep). If nothing is detectable, ask the user or default to `html-tailwind`. **Never assume a stack** — a hardcoded default silently misroutes every recommendation.
- **Reference sites the user names**: measure them instead of eyeballing screenshots. The `dembrandt` MCP reads a live URL's colors, type styles, spacing, radii, shadows, breakpoints, and motion values. It is project-scoped: add it when the design task starts with `claude mcp add dembrandt -- npx -y dembrandt@0.39.2 mcp`, and never pass `--key` (it uploads the run). Imagery, hierarchy, and grid still come from screenshots at desktop and phone width.

### Step 2: Set the design direction

Before any lookup, write the direction in a few lines: who the product is for, what it should feel like to use (one or two adjectives with a reason, not a list), what one thing will make it recognizably itself (a typographic voice, a color the category never uses, a layout move, the way it moves), and what to steer away from. Share it with the user when the task is a new page or product; a short direction is easy to correct, a finished page is not.

Name the defaults you are avoiding. Generic output comes from the same few choices, and a list of them is a better guard than "avoid a generic look":

- Inter, Roboto, or the system sans as the only typeface, at default weights
- a trust-blue primary with an orange call to action; purple-to-blue gradients; a pastel wash over white
- a centered hero with one headline, one subhead, two buttons, and a product screenshot tilted in perspective
- three feature cards in a row with an icon in a tinted circle above each
- cards with a 12px radius and a soft drop shadow on everything, including things that don't lift
- a glassmorphism panel or a bento grid chosen because it is current, not because the content is grid-shaped
- an emoji where an icon belongs

Extend the list after each first render with whatever you saw that could have been any product.

### Step 3: Generate candidates from the database

With the direction set, run `--design-system` to get pattern, style, color, typography, effect, and anti-pattern candidates, with the reasoning from `ui-reasoning.csv`:

```bash
search.py "<product_type> <industry> <keywords>" --design-system [-p "Project Name"]
```

Put the direction's words in the query, not just the product type: `"fintech dashboard dense editorial warm"` draws different rows than `"fintech dashboard"`. Read the results against the direction. Keep what serves it, replace what doesn't (a second query with different keywords, a `--domain` search, or your own choice with the reason), and say which it was. The top row is a candidate, not a decision; two products in the same category should not come out identical.

Skip the lookup only for a change that stays inside an existing design system; then read that system (below) and work within it.

**Persisting the design system (master + overrides).** To save it for later sessions, add `--persist` **and always pass `--output-dir` pointed at the project root** — without it, files are written relative to whatever directory the tool happens to run from:

```bash
search.py "<query>" --design-system --persist -p "Project Name" --output-dir "<project-root>"
```

This creates `design-system/<project-slug>/MASTER.md` (the global source of truth) and `design-system/<project-slug>/pages/` for page-specific overrides; `--page "dashboard"` also creates `pages/dashboard.md`. If `MASTER.md` already exists, `--persist` skips writing unless you also pass `--force`: check for it and read it before regenerating, so prior decisions are not discarded. Edit the persisted file to match what you actually decided; it should record the design, not the lookup.

Retrieval when building a page: read `MASTER.md`; if `pages/<page-name>.md` exists, its rules override master.

**Design dials (optional).** Three 1–10 sliders tune `--design-system` output without changing the query:

```bash
search.py "<query>" --design-system --variance <1-10> --motion <1-10> --density <1-10>
```

| Dial | Low (1-3) | Mid (4-7) | High (8-10) |
|------|-----------|-----------|-------------|
| `--variance` | Centered / minimal | Balanced / modern | Bold / asymmetric (Brutalism, Bento Grids) |
| `--motion` | Subtle micro-interactions | Standard scroll/stagger motion | Complex choreography (pin, Flip, SplitText) |
| `--density` | Spacious (24-96px spacing scale) | Standard (16-64px, default) | Dense/dashboard (8-32px spacing scale) |

`--motion` attaches a GSAP snippet matched to the tier; `--density` overrides the `--space-*` token table. An unset dial leaves that part unchanged. Set the dials from the direction (a high `--motion` is the direction overriding the animation defaults, on purpose).

### Step 4: Supplement with detailed searches (as needed)

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

### Step 5: Stack guidelines

```bash
search.py "<keyword>" --stack <stack>
```

**Available stacks:** `react`, `nextjs`, `vue`, `svelte`, `astro`, `nuxtjs`, `nuxt-ui`, `angular`, `laravel`, `swiftui`, `react-native`, `flutter`, `jetpack-compose`, `html-tailwind`, `shadcn`, `threejs`, `javafx`, `wpf`, `winui`, `avalonia`, `uno`, `uwp`. Use the stack detected in Step 1.

### Step 6: Build and check

Implement to the direction. Before showing it, check the floors (contrast, focus, labels, targets, reduced motion), then look at the render at desktop and phone width and ask whether it could be any product in its category. If it could, go back to the defaults list and change the thing that makes it so. Make it specific through design, never through facts the brief did not supply: an invented count, feature, or policy reads as true, so it is an error, not character.

## If a search returns 0 results

Do not fabricate output. Instead:

1. Retry once with broader or differently-worded keywords (try product + style separately rather than combined).
2. If still empty, design from the direction and the floors, and say that the choices came from you, not from a database match.
3. Never present a 0-result search as if it returned data.

## Example workflow

**User request:** "Make an AI search homepage." (stack detected as Next.js from `package.json`)

Direction, shared with the user: for people who run many searches a day and want the answer, not the product; it should feel quiet and fast. The one distinctive thing is the typography: a serif for the answers, large, with generous measure, so results read like a page rather than a feed. Avoid the chat-box-in-a-gradient-void that every AI product ships, the trust-blue primary, and the three-feature-card row.

```bash
# Step 3: candidates, with the direction in the query
search.py "AI search tool editorial serif quiet minimal" --design-system -p "AI Search" --motion 3 --density 4

# Step 4: supplement
search.py "serif editorial pairing" --domain typography
search.py "search loading state streaming" --domain ux

# Step 5: stack guidelines
search.py "suspense streaming bundle" --stack nextjs
```

The lookup proposes a sans pairing and a cool-gray palette; keep the gray scale, swap the type to a serif-plus-sans pairing from the typography search, and record both decisions in `MASTER.md`. Then implement and run the Step 6 check.

## Output formats

`--design-system` supports `-f ascii` (default, terminal display), `-f markdown` (documentation), and `--json` (machine-readable, includes the raw design system dict plus persistence status).

## Tips for better results

- Use **multi-dimensional keywords** — combine product + industry + tone + density: `"entertainment social vibrant content-dense"`, not just `"app"`
- Try different phrasings for the same need: `"playful neon"` → `"vibrant dark"` → `"content-first minimal"`
- Pass the detected stack explicitly for implementation-specific guidance

| Problem | What to do |
|---------|------------|
| Can't decide on style/color | Sharpen the direction first, then re-run `--design-system` with its words |
| Dark mode contrast issues | [references/quick-reference.md](references/quick-reference.md) §6: `color-dark-mode` + `color-accessible-pairs` |
| Animations feel unnatural | §7: `spring-physics` + `easing` + `exit-faster-than-enter` |
| Form UX is poor | §8: `inline-validation` + `error-clarity` + `focus-management` |
| Navigation feels confusing | §9: `nav-hierarchy` + `bottom-nav-limit` + `back-behavior` |
| Layout breaks on small screens | §5: `mobile-first` + `breakpoint-consistency` |
| Performance / jank | §3: `virtualize-lists` + `main-thread-budget` + `debounce-throttle` |

## Before delivering app UI

For native/mobile app UI (iOS/Android/React Native/Flutter), read [references/pro-rules.md](references/pro-rules.md) and run through its pre-delivery checklist: icon/visual-element discipline, interaction feedback, light/dark contrast, safe-area layout, accessibility.
