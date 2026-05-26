<!-- RESEARCH_DATE: 2026-03-11 -->
# A/B Testing Patterns for Ecommerce

Actionable patterns for scaffolding, prioritizing, and measuring A/B tests on ecommerce stores.

## Testing Fundamentals

### Hypothesis Format
Every test needs a written hypothesis BEFORE implementation:
```
If we [change], then [metric] will [improve/decrease] by [amount],
because [rationale based on evidence].
```

### Control vs Variant
- **Control**: The current live experience (no changes)
- **Variant**: The modified experience (one change only)
- Always run both simultaneously with random assignment
- Never compare "before" vs "after" time periods — too many confounding variables

## Statistical Significance

### Minimum Requirements
| Metric | Minimum |
|--------|---------|
| Unique visitors per variant | 5,000 |
| Conversions per variant | 100 |
| Test duration | 14 days (captures weekly cycles) |
| Confidence level | 95% (standard) |
| Statistical power | 80% |

### Traffic-to-Duration Guide
| Monthly Traffic | Baseline CVR | Detectable Lift | Min Duration |
|----------------|-------------|-----------------|--------------|
| 100k visitors | 3% | 10% relative | ~2 weeks |
| 50k visitors | 3% | 15% relative | ~3 weeks |
| 20k visitors | 3% | 20% relative | ~4-6 weeks |
| 10k visitors | 3% | 25% relative | ~6-8 weeks |
| <5k visitors | any | unreliable | Do NOT A/B test |

### Frequentist vs Bayesian
- **Frequentist**: Fixed sample size, no peeking, binary result. Used by Optimizely.
- **Bayesian**: Allows peeking, gives probability of winning. Used by VWO, Convert.
- For stores <50k monthly visitors: prefer Bayesian tools.

## When NOT to Test

### Skip testing when:
- **Traffic too low**: <1,000 visitors/week to the target page
- **Obvious fix**: Broken checkout, missing CTAs, 404s, slow loads
- **Compliance/legal**: Privacy policy, GDPR, accessibility fixes
- **Proven best practices**: Trust badges at checkout, mobile responsiveness, basic reviews
- **No measurement**: Analytics not set up — fix that first
- **Micro-changes**: Button color tweaks on <100k traffic — won't reach significance

### Low-Traffic Alternatives
- User testing (watch 5 people use the store)
- Heatmaps and session recordings (Hotjar, Clarity)
- Post-purchase surveys ("What almost stopped you from buying?")
- Before/after week-over-week analysis
- Sequential testing with longer observation windows

## ICE Scoring for Test Prioritization

### Formula
```
ICE Score = Impact (1-10) x Confidence (1-10) x Ease (1-10)
```

### Scoring Guide
**Impact** — How much will this move the metric?
- 1-3: Cosmetic (button color, font) | 4-6: Moderate (new layout, copy) | 7-10: Significant (checkout redesign, pricing)

**Confidence** — How sure are you?
- 1-3: Gut feeling | 4-6: Industry benchmarks | 7-10: Your own data/research

**Ease** — How hard to implement?
- 1-3: Weeks of dev | 4-6: Days | 7-10: Hours or minutes

### Example Scores
| Test Idea | I | C | E | ICE |
|-----------|---|---|---|-----|
| Add "Only X left" to product page *(→ see ethics-gate.md §1.1 — fabricated scarcity is a BLOCK regardless of A/B methodology; only test this with truthful inventory data)* | 6 | 7 | 9 | 378 |
| Test free shipping threshold | 8 | 6 | 8 | 384 |
| Add customer reviews | 7 | 8 | 6 | 336 |
| CTA "Add to Cart" vs "Buy Now" | 5 | 5 | 10 | 250 |
| Redesign entire checkout | 9 | 5 | 2 | 90 |

### Process
1. Brainstorm 15-30 test ideas
2. Score each independently
3. Sort descending, run top-scoring first
4. Re-score quarterly as you learn what works

## Shopify Testing Patterns

### Native: Shopify Rollouts (Winter 2026)
- Built into admin: Online Store > Themes
- No app install, no extra cost
- Duplicates entire theme for variant — theme-level splits only
- No element-level testing, no segmentation, limited stats
- Best for: Simple layout A/B (new homepage vs old)
- **Note: split-testing analytics and traffic allocation (true A/B experiment mode) require Advanced plan or higher.** Basic/standard Shopify plans get scheduled deployments only — not split testing with analytics. [**AUDIT 2026-04-22: confirmed by Shopify Help Center + CharleAgency guide spot-check.**]

### Third-Party Apps
*Pricing current as of 2026-03-11 — re-verify before citing. Shoplift pricing is traffic-tiered; $74 is the entry tier.* [**AUDIT 2026-04-22: date-stamped; Shoplift confirmed traffic-tiered, not flat-rate.**]

| Tool | Best For | From |
|------|----------|------|
| Shoplift | Page element testing | $74/mo (entry tier; traffic-tiered) |
| Intelligems | Price/shipping/offer testing | $99/mo |
| Visually | Full-funnel no-code testing | Free plan |
| OptiMonk | Popup/overlay testing | Free plan |

### Liquid Variant Pattern (DIY)
```liquid
{% assign variant = customer.id | modulo: 2 %}
{% if variant == 0 %}
  {% render 'cta-control' %}
{% else %}
  {% render 'cta-variant-a' %}
{% endif %}
```
Limitation: Only works for logged-in customers. For anonymous visitors, use a third-party app or cookie-based JS split.

## Next.js Testing Patterns

### Middleware Split (Recommended)
```typescript
// middleware.ts
import { NextRequest, NextResponse } from 'next/server';

const COOKIE = 'exp-variant';
const VARIANTS = ['control', 'variant-a'];

export function middleware(request: NextRequest) {
  const existing = request.cookies.get(COOKIE)?.value;
  const variant = existing || VARIANTS[Math.random() < 0.5 ? 0 : 1];

  const url = request.nextUrl.clone();
  url.pathname = `/${variant}${url.pathname}`;

  const response = NextResponse.rewrite(url);
  if (!existing) {
    response.cookies.set(COOKIE, variant, { maxAge: 60 * 60 * 24 * 30 });
  }
  return response;
}
```

### Why Middleware?
- Server-side assignment = zero client flicker, zero CLS
- Cookie persists variant across sessions
- Rewrite is invisible to user (URL doesn't change)

### Vercel Edge Config
- Store experiment definitions in Edge Config (P99 <15ms reads)
- Auto-syncs with Statsig or Optimizely via webhooks
- Free tier includes Edge Config

### Partial Prerendering (PPR)
Static shell cached at edge + dynamic experiment slots stream in. Best performance for headless storefronts running experiments.

## GA4 Measurement (Any Platform)

### DIY Split + GA4 Custom Dimension
1. Assign variant via localStorage (or cookie for SSR)
2. Push to dataLayer: `{ experiment_variant: 'control' }`
3. Register `experiment_variant` as User-scoped custom dimension in GA4
4. Analyze in Explore > Free form, dimension = experiment_variant
5. Check significance externally (statsig.com/calculator)

### GA4 + Microsoft Clarity (Free)
- Clarity auto-integrates with GA4
- Filter session recordings by experiment variant
- Quantitative (GA4) + qualitative (Clarity) in one workflow

### Limitations of DIY GA4
- No automatic splitting, significance calculation, or visual editor
- Risk of flicker with client-side assignment
- Suitable for 1-2 concurrent tests max

## Common Mistakes

1. **Testing multiple variables** — Test ONE thing per experiment
2. **Stopping early** — Never stop because one variant "looks like it's winning"
3. **Ignoring segments** — Overall flat result may hide a win in mobile or new visitors
4. **Making changes mid-test** — Invalidates all collected data
5. **No documentation** — Record hypothesis, dates, traffic, result, and learnings
6. **Testing on low-traffic pages** — Results take months and remain inconclusive
7. **Peeking with frequentist tools** — Inflates false positive rate; use Bayesian if you must peek
8. **Not pre-calculating sample size** — Know your required N before starting

## Decision Tree

```
Have >5,000 monthly visitors to target page?
├── NO → Use qualitative methods (heatmaps, surveys, user testing)
└── YES → Is change a bug fix, compliance, or proven best practice?
    ├── YES → Just implement it
    └── NO → What platform?
        ├── Shopify → Shoplift/Intelligems (budget) or Rollouts/Visually (free)
        ├── Next.js on Vercel → Edge Config + Statsig template
        ├── Next.js elsewhere → Middleware + cookie-based DIY
        └── Any platform, minimal → GA4 custom dimension + manual split
```
