# Cluster: visual-cta (laptop)

## Findings

```
FINDING: FAIL
TITLE: Add to Cart Button Low Contrast
SECTION: primary-cta
ELEMENT: button.btn-cart
SOURCE: VISUAL
OBSERVATION: The primary Add to Cart button blends into the page background with insufficient contrast for quick recognition.
RECOMMENDATION: Increase the button background to a high-contrast accent color so the purchase action is the most visually dominant element above the fold.
REFERENCE: cta-design-and-placement.md:Finding 3
PRIORITY: HIGH
**Why this matters:** Low-contrast primary CTAs reduce conversion because visitors cannot quickly identify where to click to purchase.
↳ cta-design-and-placement.md, Finding 3 (Fixture, 2024) [Silver]
```

```
FINDING: FAIL
TITLE: CTA Placement Sits Below Fold
SECTION: cta-placement
ELEMENT: button.btn-cart
SOURCE: VISUAL
OBSERVATION: The Add to Cart button is positioned below the initial viewport, requiring a scroll before the purchase path becomes visible.
RECOMMENDATION: Elevate the button into the first screenful, or add a sticky CTA that surfaces once the visitor scrolls past the initial position.
REFERENCE: cta-design-and-placement.md:Finding 11
PRIORITY: MEDIUM
**Why this matters:** Above-fold CTAs convert consistently better because they shorten the path between interest and action.
↳ cta-design-and-placement.md, Finding 11 (Fixture, 2024) [Bronze]
```

## What's Working Well

- **hero-layout**: Product title reads clearly and sits above the price. ↳ hero-section-psychology.md, Finding 1
